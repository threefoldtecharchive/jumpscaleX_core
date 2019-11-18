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
            self._gedis_server = j.servers.gedis.get(name="%s_gedis_threebot" % self.name, port=8901)
            self._gedis_server._threebot_server = self
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

    def bcdb_get(self, name):

        if j.data.bcdb.exists(name=name):
            bcdb = j.data.bcdb.get(name=name)
            if bcdb.storclient.type == "zdb":
                zdb_admin = j.clients.zdb.client_admin_get()
                zdb_namespace_exists = zdb_admin.namespace_exists(name)
                if not zdb_namespace_exists:
                    # can't we put logic into the bcdb-new to use existing namespace if its there and recreate the index
                    raise j.exceptions.Base("serious issue bcdb exists, zdb namespace does not")
            return bcdb

        return j.data.bcdb.new(name=name)

    @property
    def zdb(self):
        if not self._zdb:
            self._zdb = j.servers.zdb.get(
                name=f"{self.name}_zdb_threebot", adminsecret_=self.adminsecret_, executor=self.executor
            )
        return self._zdb

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

        while True:
            # check all models are mapped to global namespace
            for bcdb in j.data.bcdb.instances:
                if bcdb.name not in j.threebot.bcdb.__dict__:
                    j.threebot.bcdb.__dict__[bcdb.name] = bcdb.children
                    print("AAA")

            # check state workers
            for key, worker in j.threebot.myjobs.workers._children.items():
                # get status from worker
                worker.load()

            # remove jobs from _children older than 1 day
            # copy jobs, because we will modify children inside the loop
            jobs = dict(j.threebot.myjobs.jobs._children.items())
            for key, job in jobs.items():
                job.load()
                if job.time_stop > 0:
                    if job.time_stop < j.data.time.epoch - 600:
                        j.threebot.myjobs.jobs._children.pop(job.name)

            # unbind old jobs from namespace
            self._log_debug("maintenance")

            gevent.sleep(10)

    def _maintenance_day(self):

        day1 = 3600 * 24

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

            ##SHOULD NOT BE NEEDED
            # j.data.bcdb.check()

            if restart or j.sal.nettools.tcpPortConnectionTest("localhost", 9900) == False:
                self.zdb.start()

            if restart or j.sal.nettools.tcpPortConnectionTest("localhost", 1491) == False:
                j.servers.sonic.default.start()

            # add system actors and basic chat flows
            self.gedis_server.actors_add("%s/base_actors" % self._dirpath)
            self.gedis_server.chatbot.chatflows_load("%s/base_chatflows" % self._dirpath)
            self.rack_server.add("gedis", self.gedis_server.gevent_server)

            bcdb = j.data.bcdb.system
            redis_server = bcdb.redis_server_get(port=6380, secret="123456")
            self.rack_server.add("bcdb_system_redis", redis_server.gevent_server)
            # FIXME: the package_manager actor doesn't properly load the package (web interface)

            if restart or j.sal.nettools.tcpPortConnectionTest("localhost", 80) == False:
                self._log_info("OPENRESTY START")
                if restart:
                    self.openresty_server.stop()
                self.openresty_server.start()

            j.tools.threebot_packages.get(
                "webinterface",
                path=j.core.tools.text_replace(
                    "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot/webinterface/"
                ),
            )
            j.tools.threebot_packages.get(
                "wiki",
                path=j.core.tools.text_replace(
                    "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot/wiki/"
                ),
            )
            j.tools.threebot_packages.get(
                "chat",
                path=j.core.tools.text_replace(
                    "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot/chat/"
                ),
            )
            j.tools.threebot_packages.get(
                "myjobs",
                path=j.core.tools.text_replace(
                    "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot/myjobs"
                ),
            )
            j.tools.threebot_packages.get(
                "packagemanagerui",
                path=j.core.tools.text_replace(
                    "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot/packagemanagerui"
                ),
            )

            self._log_info("start workers")

            self.rack_server.start(wait=False)

            j.servers.myjobs.workers_tmux_start(2, in3bot=True)
            # j.servers.myjobs._workers_gipc_nr_max = 10
            # j.servers.myjobs.workers_subprocess_start()

            self._log_info("start workers done")

            # remove the package

            j.threebot.servers = Servers()
            j.threebot.servers.zdb = j.servers.zdb.default_zdb_threebot
            j.threebot.servers.gedis = j.servers.gedis.default_gedis_threebot
            j.threebot.servers.web = j.servers.threebot.default.openresty_server
            j.threebot.servers.core = j.servers.threebot.default
            j.threebot.servers.gevent_rack = j.servers.threebot.default.rack_server
            j.threebot.myjobs = j.servers.myjobs
            # j.threebot.bcdb_get = j.servers.threebot.bcdb_get
            j.threebot.bcdb = BCDBS()

            j.threebot.servers.gevent_rack.greenlet_add("maintenance", self._maintenance)

            # add user added packages
            for package in j.tools.threebot_packages.find():
                if package.status == "INIT":
                    self._log_warning("PREPARE:%s" % package.name)
                    package.prepare()
                    package.status = "INSTALLED"
                    package.save()
                if package.status not in ["disabled"]:
                    self._log_warning("START:%s" % package.name)
                    package.start()
                    package.status = "RUNNING"
                    package.save()
                    # try:
                    #     package.start()
                    # except Exception as e:
                    #     j.core.tools.log(level=50, exception=e, stdout=True)
                    #     package.status = "error"

            self._packages_walk()
            j.threebot.__dict__.pop("package")
            # j.__dict__.pop("servers")
            j.__dict__.pop("builders")
            # j.__dict__.pop("shell")
            # j.__dict__.pop("shelli")
            j.__dict__.pop("tutorials")
            j.__dict__.pop("sal_zos")

            # reload nginx at the end after loading packages and its config is written
            j.servers.threebot.current.openresty_server.reload()

            print("*** 3BOTSERVER IS RUNNING ***")
            # j.shell()
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

    def _packages_walk(self):

        path = j.core.tools.text_replace("{DIR_CODE}/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/")
        j.threebot.__dict__["packages"] = Packages()

        def process(path, arg):
            if j.sal.fs.getBaseName(path) == "package.py":
                path = j.sal.fs.getDirName(path)
                path = path.rstrip("/")
                splitted = path.split("/")
                u = splitted.index("ThreeBotPackages")
                name = "__".join(splitted[u + 1 :])
                # packagename = os.path.basename(path)
                if not name in j.threebot.packages.__dict__:
                    if j.tools.threebot_packages.exists(name):
                        p = j.tools.threebot_packages.get(name)
                        p.start()
                        j.threebot.packages.__dict__[name] = p
                    else:
                        j.threebot.packages.__dict__[name] = PackageInstall(name=name, path=path)

            return

        def callbackForMatchDir(path, arg):
            if j.sal.fs.getBaseName(path) in [
                "frontend",
                "packagemanagerui",
                "wiki",
                "actors",
                "models",
                "bottle",
                "html",
                "static",
                "tests",
                "templates",
                "macros",
                "jobvis",
            ]:
                return False
            if not j.sal.fs.getBaseName(path).startswith("_"):
                return True
            # return j.sal.fs.exists(j.sal.fs.joinPaths(path, "package.py"))

        j.sal.fswalker.walkFunctional(path, callbackFunctionFile=process, callbackForMatchDir=callbackForMatchDir)

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
