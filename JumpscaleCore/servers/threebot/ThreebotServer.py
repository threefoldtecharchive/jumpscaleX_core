from Jumpscale import j
import os
import gevent
import time
from gevent import event
import os

# from .OpenPublish import OpenPublish

JSConfigs = j.baseclasses.object_config_collection


class Actors:
    pass


class Servers:
    pass


class BCDBS:
    pass


class Packages:
    pass


class PackageInstall(j.baseclasses.object):
    def _init(self, name=None, path=None):
        self.path = path
        self.name = name
        self._zdb = None
        self._sonic = None

    def install(self):
        server = j.servers.threebot.default
        package = j.tools.threebot_packages.get(self.name, path=self.path, threebot_server_name=server.name)
        package.prepare()
        package.save()
        name = self.name
        package.start()
        j.threebot.packages.__dict__[self.name] = package
        return "OK"


class ThreeBotServer(j.baseclasses.object_config):
    """
    Threebot server
    """

    _SCHEMATEXT = """
        @url = jumpscale.threebot_server.1
        name** = "main" (S)
        executor = tmux,corex (E)
        adminsecret_ = "123456"  (S)
        state = "init,installed"
        ssl = (B)
        web =  (B)
        """

    def _init(self, **kwargs):
        self._rack_server = None
        self._gedis_server = None
        self._openresty_server = None
        self._startup_cmd = None
        self._zdb = None
        self.threebot_server = None
        self.web = False
        self.ssl = False
        self.client = None
        j.servers.threebot.current = self

        if self.state == "init":
            j.tools.threebot_packages.load()
            self.state = "installed"

    @property
    def secret(self):
        return self.adminsecret_

    @property
    def rack_server(self):
        if not self._rack_server:
            self._rack_server = j.servers.rack.get()
        return self._rack_server

    @property
    def gedis_server(self):
        if not self._gedis_server:
            adminsecret_ = j.data.hash.md5_string(self.adminsecret_)
            self._gedis_server = j.servers.gedis.get(name="threebot", port=8901, secret_=adminsecret_)
        return self._gedis_server

    @property
    def openresty_server(self):
        if not self._openresty_server:
            j.servers.openresty.install()
            self._openresty_server = j.servers.openresty.get(
                name=f"{self.name}_openresty_threebot", executor=self.executor
            )
            self._openresty_server.install()
        return self._openresty_server

    def bcdb_get(self, namespace, ttype, instance):
        if ttype not in ["zdb", "sqlite"]:
            raise j.exceptions.Input("ttype can only be zdb or sqlite")

        name = "threebot_%s_%s" % (ttype, namespace)

        if j.data.bcdb.exists(name=name):
            bcdb = j.data.bcdb.get(name=name)
            if bcdb.storclient.type == "zdb":
                if not ttype == "zdb":
                    raise j.exceptions.Base("type of storclient needs to be zdb")
                zdb_admin = j.clients.zdb.client_admin_get()
                zdb_namespace_exists = zdb_admin.namespace_exists(name)
                if not zdb_namespace_exists:
                    # can't we put logic into the bcdb-new to use existing namespace if its there and recreate the index
                    raise j.exceptions.Base("serious issue bcdb exists, zdb namespace does not")
            else:
                if not ttype == "sqlite":
                    raise j.exceptions.Base("type of storclient needs to be sqlite")

            return bcdb

        return j.data.bcdb.new(name=name)

    @property
    def zdb(self):
        if not self._zdb:
            self._log_info("start zdb")
            self._sonic, self._zdb = j.data.bcdb.threebot_zdb_sonic_start()
        return self._zdb

    @property
    def sonic(self):
        if not self._sonic:
            self._log_info("start sonic")
            self._sonic, self._zdb = j.data.bcdb.threebot_zdb_sonic_start()
        return self._sonic

    def _proxy_create(self, name, port_source, port_dest, scheme_source="https", scheme_dest="http", ptype="http"):
        """
        creates reverse proxy for ports
        :return:
        """
        website = self.openresty_server.websites.get(f"{name}_websites")
        website.ssl = scheme_source == "https"
        website.port = port_source
        locations = website.locations.get(name)
        proxy_location = locations.locations_proxy.new()
        proxy_location.name = name
        proxy_location.path_url = "/"
        proxy_location.ipaddr_dest = "0.0.0.0"
        proxy_location.port_dest = port_dest
        proxy_location.type = ptype
        proxy_location.scheme = scheme_dest
        locations.configure()
        website.configure()

    def _maintenance(self):

        # check all models are mapped to global namespace
        for bcdb in j.data.bcdb.instances.values():
            if bcdb.name not in j.threebot.bcdb.__dict__:
                j.threebot.bcdb.__dict__[bcdb.name] = bcdb.children

        # check state workers
        for key, worker in j.threebot.myjobs.workers._children.items():
            # get status from worker
            worker.load()

        # remove jobs from _children older than 1 day
        keys = [key for key in j.threebot.myjobs.jobs._children.keys()]
        for key in keys:
            if key in j.threebot.myjobs.jobs._children:
                job = j.threebot.myjobs.jobs._children[key]
                job.load()
                if job.time_stop > 0:
                    if job.time_stop < j.data.time.epoch - 600:
                        j.threebot.myjobs.jobs._children.pop(job.name)

    def _maintenance_day(self):

        while True:
            # remove jobs older than 1 day
            for job in j.threebot.myjobs.jobs.find():
                if job.time_stop > 0:
                    if job.time_stop < j.data.time.epoch - day1:
                        job.delete()

            gevent.sleep(day1)

    def start(self, background=False, restart=False):
        """

        kosmos -p 'j.servers.threebot.default.start(background=True)'
        kosmos -p 'j.servers.threebot.default.start(background=False)'

        :param background: if True will start all servers including threebot itself in the background

        ports & paths used for threebotserver
        see: {DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/docs/3Bot/web_environment.md

        """

        self.save()

        if not background:

            j.servers.myjobs.reset_data()
            self.zdb  # will start sonic & zdb
            self.sonic

            ##SHOULD NOT BE NEEDED
            # j.data.bcdb.check()

            # add system actors and basic chat flows
            self.gedis_server.actors_add("%s/base_actors" % self._dirpath)
            self.gedis_server.chatbot.chatflows_load("%s/base_chatflows" % self._dirpath)
            self.rack_server.add("gedis", self.gedis_server.gevent_server)

            # needed for myjobs
            bcdb = j.data.bcdb.system
            adminsecret_ = j.data.hash.md5_string(self.adminsecret_)
            redis_server = bcdb.redis_server_get(port=6380, secret=adminsecret_)
            # just to make sure we don't have it open to external
            assert redis_server.host == "127.0.0.1"
            assert redis_server.secret == adminsecret_
            self.rack_server.add("bcdb_system_redis", redis_server.gevent_server)

            if restart or j.sal.nettools.tcpPortConnectionTest("localhost", 80) == False:
                self._log_info("OPENRESTY START")
                if restart:
                    self.openresty_server.stop()
                self.openresty_server.start()
            else:
                self.openresty_server.reload()

            self._log_info("start workers")

            self.rack_server.start(wait=False)

            # j.servers.myjobs.workers_tmux_start(2, in3bot=True)
            j.servers.myjobs._workers_gipc_nr_max = 10
            j.servers.myjobs.workers_subprocess_start()

            self._log_info("start workers done")

            # remove the package

            j.threebot.servers = Servers()
            j.threebot.servers.zdb = self.zdb
            j.threebot.servers.zonic = self.sonic
            j.threebot.servers.gedis = self.gedis_server
            j.threebot.servers.web = self.openresty_server
            j.threebot.servers.core = self
            j.threebot.servers.gevent_rack = self.rack_server
            j.threebot.myjobs = j.servers.myjobs
            # j.threebot.bcdb_get = j.servers.threebot.bcdb_get
            j.threebot.bcdb = BCDBS()
            j.threebot.bcdb_factory = j.data.bcdb

            # j.threebot.servers.gevent_rack.greenlet_add("maintenance", self._maintenance)
            self._maintenance()

            self._packages_install()
            # add user added packages
            for package in j.tools.threebot_packages.find():
                # if package.status == "INIT":
                #     self._log_warning("PREPARE:%s" % package.name)
                #     try:
                #         package.prepare()
                #         package.status = "INSTALLED"
                #         package.save()
                #     except Exception as e:
                #         self._log_error("could not install package:%s" % package.name)
                #         j.core.tools.log(level=50, exception=e, stdout=True)
                if package.status in ["installed", "error"]:
                    self._log_warning("START:%s" % package.name)
                    try:
                        package.start()
                    except Exception as e:
                        j.core.tools.log(level=50, exception=e, stdout=True)
                        package.status = "error"
                    package.save()

            j.threebot.__dict__.pop("package")
            # LETS NOT DO SERVERS YET, STILL BREAKS TOO MUCH
            # j.__dict__.pop("servers")
            j.__dict__.pop("builders")
            # j.__dict__.pop("shell")
            # j.__dict__.pop("shelli")
            j.__dict__.pop("tutorials")
            j.__dict__.pop("sal_zos")

            # reload nginx at the end after loading packages and its config is written
            j.threebot.servers.core.openresty_server.reload()

            print("*****************************")
            print("*** 3BOTSERVER IS RUNNING ***")
            print("*****************************")
            j.shell()  # DO NOT REMOVE THIS SHELL
            forever = event.Event()
            try:
                forever.wait()
            except KeyboardInterrupt:
                self.stop()
            return

        else:
            if not self.startup_cmd.is_running():
                self.startup_cmd.start()
                time.sleep(1)

        if not j.sal.nettools.waitConnectionTest("127.0.0.1", 8901, timeout=600):
            raise j.exceptions.Timeout("Could not start threebot server")

        self.client = j.clients.gedis.get(name="threebot", port=8901, namespace="default")
        # TODO: will have to authenticate myself

        self.client.reload()
        assert self.client.ping()

        return self.client

    def _packages_install(self):

        if not j.tools.threebot_packages.exists(name="threefold.webinterface"):
            j.tools.threebot_packages.load()

        names = ["webinterface", "wiki", "chat", "myjobs", "packagemanagerui"]
        names = ["webinterface"]  # TODO: TEST REMOVE
        for name in names:
            p = j.tools.threebot_packages.get(name=f"threefold.{name}")
            p.install()

    # def _packages_walk(self):
    #
    #     j.threebot.__dict__["packages"] = Packages()
    #     if not name in j.threebot.packages.__dict__:
    #         if j.tools.threebot_packages.exists(name):
    #             p = j.tools.threebot_packages.get(name)
    #             # DONT START, has already been done up
    #             j.threebot.packages.__dict__[name] = p
    #         else:
    #             j.threebot.packages.__dict__[name] = PackageInstall(name=name, path=path)

    def stop(self):
        """
        :return:
        """
        self.startup_cmd.stop(waitstop=False, force=True)
        self.openresty_server.stop()

    @property
    def startup_cmd(self):
        if self.web:
            web = "True"
        else:
            web = "False"
        cmd_start = """
        from gevent import monkey
        monkey.patch_all(subprocess=False)
        from Jumpscale import j
        server = j.servers.threebot.get("{name}", executor='{executor}', web={web})
        server.start(background=False)
        """.format(
            name=self.name, executor=self.executor, web=web
        )
        cmd_start = j.core.tools.text_strip(cmd_start)
        startup = j.servers.startupcmd.get(name="threebot_{}".format(self.name), cmd_start=cmd_start)
        startup.executor = self.executor
        startup.interpreter = "python"
        startup.timeout = 600
        startup.ports = [9900, 1491, 8901]
        if self.web:
            startup.ports += [80, 443, 4444, 4445]
        return startup
