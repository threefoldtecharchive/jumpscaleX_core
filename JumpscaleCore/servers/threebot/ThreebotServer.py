from Jumpscale import j
import os
import gevent
import time

# from .OpenPublish import OpenPublish

JSConfigs = j.baseclasses.object_config_collection


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

    def start(self, background=False, web=None, ssl=None, timeout=120):
        """

        kosmos -p 'j.servers.threebot.default.start(background=True,web=False)'
        kosmos -p 'j.servers.threebot.default.start(background=False,web=False)'

        :param background: if True will start all servers including threebot itself in the background

        ports & paths used for threebotserver
        see: /sandbox/code/github/threefoldtech/jumpscaleX_core/docs/3Bot/web_environment.md

        """
        if web is None:
            web = self.web
        else:
            self.web = web

        if ssl is None:
            ssl = self.ssl
        else:
            self.ssl = ssl

        self.save()

        if not background:

            self.zdb.start()
            j.servers.sonic.default.start()

            # add system actors and basic chat flows
            self.gedis_server.actors_add("%s/base_actors" % self._dirpath)
            self.gedis_server.chatbot.chatflows_load("%s/base_chatflows" % self._dirpath)
            self.rack_server.add("gedis", self.gedis_server.gevent_server)

            bcdb = j.data.bcdb.system
            redis_server = bcdb.redis_server_get(port=6380, secret="123456")
            self.rack_server.add("bcdb_system_redis", redis_server.gevent_server)
            # FIXME: the package_manager actor doesn't properly load the package (web interface)

            j.tools.threebot_packages.get(
                "webinterface",
                path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/threebot/webinterface/",
            )
            j.tools.threebot_packages.get(
                "wiki", path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/threebot/wiki/"
            )
            j.tools.threebot_packages.get(
                "chat", path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/threebot/chat/"
            )

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
            if web:
                self._log_info("OPENRESTY START")
                self.openresty_server.start()
                # for in case was already loaded
                j.servers.threebot.current.openresty_server.reload()
            self.rack_server.start()

        else:
            if not self.startup_cmd.is_running():
                self.startup_cmd.start()
                time.sleep(1)

        if not j.sal.nettools.waitConnectionTest("127.0.0.1", 8901, timeout=timeout):
            raise j.exceptions.Timeout("Could not start threebot server")

        self.client = j.clients.gedis.get(name="threebot", port=8901, namespace="default")
        # TODO: will have to authenticate myself

        self.client.reload()
        assert self.client.ping()

        return self.client

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
        startup.timeout = 120
        startup.ports = [9900, 1491, 8901]
        if self.web:
            startup.ports += [80, 443, 4444, 4445]
        return startup
