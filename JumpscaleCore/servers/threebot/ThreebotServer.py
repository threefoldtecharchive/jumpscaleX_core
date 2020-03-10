import os
import sys
import time

import gevent
from gevent import event

from Jumpscale import j
from Jumpscale.core.KosmosShell import LogPane

JSConfigs = j.baseclasses.object_config_collection


class Actors:
    pass


class Servers:
    pass


class BCDBS:
    pass


class Packages:
    pass


class ThreeBotServer(j.baseclasses.object_config):
    """
    Threebot server
    """

    _SCHEMATEXT = """
        @url = jumpscale.threebot_server.1
        name** = "main" (S)
        executor = tmux,corex (E)
        adminsecret_ = ""  (S)
        state = "init,installed" (E)
        threebot_local_profile = "default" (S)
        """

    def _init(self, **kwargs):
        self._rack_server = None
        self._gedis_server = None
        self._openresty_server = None
        self._startup_cmd = None
        self._zdb = None
        self._sonic = None
        self.threebot_server = None
        self.web = False
        self.ssl = False
        self.client = None
        j.servers.threebot.current = self

        # ensure default is set for previous version
        if not self.threebot_local_profile:
            self.threebot_local_profile = "default"

        # if "adminsecret" in kwargs:
        #     secret = kwargs["adminsecret"]
        # elif "adminsecret_" in kwargs:
        #     secret = kwargs["adminsecret_"]
        # elif "secret" in kwargs:
        #     secret = kwargs["secret"]
        # else:
        #     secret = j.core.myenv.adminsecret

        if not self.adminsecret_:
            self.adminsecret_ = j.core.myenv.adminsecret
            assert self.adminsecret_

        if self.executor == "corex":
            raise j.exceptions.Input("only tmux supported for now")

    @property
    def secret(self):
        if self.adminsecret_ == "":
            raise j.exceptions.Input("please use ")
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
            self._gedis_server = j.servers.gedis.get(
                name="threebot", port=8901, secret_=adminsecret_, threebot_local_profile=self.threebot_local_profile
            )
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
                j.threebot.bcdb.__dict__[bcdb.name] = bcdb.models

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
        day1 = 24 * 3600
        while True:
            # remove jobs older than 1 day
            for job in j.threebot.myjobs.jobs.find():
                if job.time_stop > 0:
                    if job.time_stop < j.data.time.epoch - day1:
                        job.delete()

            gevent.sleep(day1)

    def start(self, background=False, restart=False, packages=None, with_shell=True):
        """

        kosmos -p 'j.servers.threebot.default.start(background=True)'
        kosmos -p 'j.servers.threebot.default.start(background=False)'

        :param background: if True will start all servers including threebot itself in the background
        :param packages: a list of package paths to load by default
        :type packages: list of str
        ports & paths used for threebotserver
        see: {DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/docs/3Bot/web_environment.md
        :param with_shell: if set, will run j.shell() after a successful start, defaults to True
        :type with_shell: bool
        """
        assert self._autosave  # needs to autosave or does not work well

        packages = packages or []
        self.save()
        if not background:
            j.servers.threebot._threebot_starting()
            self.zdb  # will start sonic & zdb
            self.sonic

            # now we are ready to start the jobs
            self.myjobs_start()

            j.threebot.servers = Servers()
            j.threebot.servers.zdb = self.zdb
            j.threebot.servers.sonic = self.sonic
            j.threebot.servers.gedis = self.gedis_server
            j.threebot.servers.web = self.openresty_server
            j.threebot.servers.core = self
            j.threebot.servers.gevent_rack = self.rack_server
            j.threebot.bcdb = j.data.bcdb._children

            # to allow gedis server to get the right package
            j.threebot.package_get = self.package_get
            j.threebot.actor_get = self.actor_get

            # add system actors and basic chat flows
            self.rack_server.add("gedis", self.gedis_server.gevent_server)

            # needed for myjobs (is bcdb redis server)
            adminsecret_ = j.data.hash.md5_string(self.adminsecret_)
            redis_server = j.data.bcdb.redis_server_get(port=6380, secret=adminsecret_)
            # just to make sure we don't have it open to external
            assert redis_server.host == "127.0.0.1"
            assert redis_server.secret == adminsecret_
            self.rack_server.add("bcdb_system_redis", redis_server.gevent_server)

            self._log_info("OPENRESTY START")
            self.openresty_server.start()

            # will also find all packages
            self._packages_core_init()

            # LETS NOT DO SERVERS YET, STILL BREAKS TOO MUCH
            # j.__dict__.pop("servers")
            # j.__dict__.pop("builders")
            # j.__dict__.pop("shell")
            # j.__dict__.pop("shelli")
            if j.__dict__.get("tutorials") != None:
                j.__dict__.pop("tutorials")
            if j.__dict__.get("sal_zos") != None:
                j.__dict__.pop("sal_zos")

            # at this point all packages are known but all in config mode, not installed yet
            # all internal services started but not the gevent rack yet, and should be like this

            # if someone passed along packages  (lazy loading will work for actor, package management in process)
            for path in packages:
                j.threebot.packages.zerobot.packagemanager.actors.package_manager.package_add(
                    path=path, install=False, reload=False
                )

            for package in j.tools.threebot_packages.find():

                if package.status in ["toinstall"]:
                    self._log_info("INSTALL:%s" % package.name)
                    package.install()

                if package.status in ["tostart", "installed", "error"]:
                    self._log_info("START:%s" % package.name)
                    try:
                        package.start()
                    except Exception as e:
                        j.core.tools.log(level=50, exception=e, stdout=True)
                        package.status = "error"
                    package.save()

            # reload nginx at the end after loading packages and its config is written
            self.openresty_server.reload()

            # only now we want to start the external components
            self.rack_server.start(wait=False)

            # lets wait till the gevent servers are active (e.g. gedis redis server)
            timeout2 = j.data.time.epoch + 2
            while j.data.time.epoch < timeout2:
                res = j.sal.nettools.tcpPortConnectionTest("localhost", 6380, timeout=0.1)
                j.core.db.delete("threebot.starting")
                if res:
                    break

            self._log_info("start workers")

            # j.threebot.servers.gevent_rack.greenlet_add("maintenance", self._maintenance)
            self._maintenance()

            print("*****************************")
            print("*** 3BOTSERVER IS RUNNING ***")
            print("*****************************")
            j.core.db.delete("threebot.starting")  # remove the marker in redis so we know we started

            p = j.threebot.packages
            LogPane.Show = False

            if with_shell:
                j.shell()  # for now removed otherwise debug does not work

            forever = event.Event()
            try:
                forever.wait()
            except KeyboardInterrupt:
                print("KEYB INTERUPT")

            # dont call stop
            # delete the fact that maybe we are still in starting mode
            j.data.bcdb._master_set(False)
            sys.exit()
        else:
            cmd = self.get_startup_cmd(packages=packages)
            if not cmd.is_running():
                cmd.start()
                time.sleep(1)

        # wait on lapis to start so we make sure everything is loaded by then.
        if not j.sal.nettools.waitConnectionTest("127.0.0.1", 80, timeout=600):
            raise j.exceptions.Timeout("Could not start threebot server")

        if not j.sal.nettools.waitConnectionTest("127.0.0.1", 8901, timeout=60):
            raise j.exceptions.Timeout("Could not start threebot server")

        # it happens that the server starts listening but not ready yet will try again
        retries = 60
        last_error = None

        identity = j.tools.threebot.me.get(self.threebot_local_profile, needexist=False)
        nacl = identity.nacl

        for _ in range(retries):
            try:
                client = j.clients.gedis.get(name="threebot", port=8901, server_pk_hex=nacl.verify_key_hex)
                client.reload()
                assert client.ping()
                self.client = client
                return self.client
            except Exception as e:
                time.sleep(1)
                last_error = e
        else:
            raise last_error
        # TODO: will have to authenticate myself

    def package_get(self, author3bot, package_name):
        if author3bot not in j.threebot.packages.__dict__:
            raise j.exceptions.Input("cannot find package '%s' in threebotserver" % author3bot)
        tbot = j.threebot.packages.__dict__[author3bot]
        if package_name not in tbot.__dict__:
            raise j.exceptions.Input("cannot find package with name:'%s' of threebot:'%s'" % (package_name, author3bot))
        return tbot.__dict__[package_name]

    def actor_get(self, author3bot, package_name, actor_name):
        p = self.package_get(author3bot=author3bot, package_name=package_name)
        if actor_name not in p.actors.keys():
            raise j.exceptions.Input(f"cannot find package from threebot:{author3bot}:{package_name}:{actor_name}")
        return p.actors[actor_name]

    def myjobs_start(self):
        j.threebot.myjobs = j.servers.myjobs
        self.myjobs_clean()  # TODO: we can clean this faster, see inside, should just destroy the db
        # j.servers.myjobs.workers_subprocess_start(2, in3bot=True)
        j.servers.myjobs.workers_tmux_start(2, in3bot=True)
        self._log_info("start workers done")

    def myjobs_clean(self):
        # for now we better delete all when starting, there is some syncing issue
        j.servers.myjobs.reset_data()
        # rebuild indexes before starting the workers to make sure they're up-to-date
        # j.servers.myjobs.model_action.model.index_rebuild()
        # j.servers.myjobs.workers._model.index_rebuild()
        # j.servers.myjobs.jobs._model.index_rebuild()

    def _packages_core_init(self):
        """
        this one registers all packages to the j.threebot.packages
        the core ones are put on to install

        :return:
        """
        if self.state == "INIT":
            self._log_info("FIND THE PACKAGES ON THE FILESYSTEM")
            j.tools.threebot_packages.load()

            names = ["base", "webinterface", "myjobs_ui", "packagemanager", "oauth2", "alerta"]
            for name in names:
                name2 = f"zerobot.{name}"
                if not j.tools.threebot_packages.exists(name=name2):
                    raise j.exceptions.Input("Could not find package:%s" % name2)
                p = j.tools.threebot_packages.get(name=name2)
                p.status = "tostart"  # means we need to start

            self.state = "INSTALLED"

        self._log_info("load all packages")
        for package in j.tools.threebot_packages.find():
            self._package_add(package)

        if "package" in j.threebot.__dict__:
            j.threebot.__dict__.pop("package")

    def _package_add(self, package):
        if not hasattr(j.threebot, "packages"):
            j.threebot.__dict__["packages"] = Packages()

        class PackageGroup:
            pass

        if package.source.threebot not in j.threebot.packages.__dict__:
            j.threebot.packages.__dict__[package.source.threebot] = PackageGroup()
        g = j.threebot.packages.__dict__[package.source.threebot]
        g.__dict__[package.source.name.replace(".", "__")] = package

    def stop(self):
        """
        Stop threebot server. Use it only when it's started using background=True
        """
        self.openresty_server.stop()
        self.startup_cmd.stop(waitstop=False, force=True)
        self._zdb = None
        self._sonic = None
        self._gedis_server = None
        self._rack_server = None
        self.client = None
        j.data.bcdb._master_set(False)

    def get_startup_cmd(self, packages=None):
        if self.web:
            web = "True"
        else:
            web = "False"
        cmd_start = """
        from gevent import monkey
        monkey.patch_all(subprocess=False)
        from Jumpscale import j
        server = j.servers.threebot.get("{name}", executor='{executor}')
        server.start(background=False, packages={packages})
        """.format(
            name=self.name, executor=self.executor, web=web, packages=packages
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

    @property
    def startup_cmd(self):
        return self.get_startup_cmd()
