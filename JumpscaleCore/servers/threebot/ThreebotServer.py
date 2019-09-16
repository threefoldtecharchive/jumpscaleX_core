from Jumpscale import j
import os
import gevent
from .OpenPublish import OpenPublish

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
            self._gedis_server = j.servers.gedis.get(name=f"{self.name}_gedis_threebot", port=8901)
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
        zdb_admin = j.clients.zdb.client_admin_get()
        if j.data.bcdb.exists(name=name):
            if not zdb_admin.namespace_exists(name):
                j.data.bcdb.destroy(name=name)
        if j.data.bcdb.exists(name=name):
            return j.data.bcdb.get(name=name)
        else:
            zdb = zdb_admin.namespace_new(name, secret=self.secret)
            return j.data.bcdb.new(name=name, storclient=zdb)

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

    def _init_web(self, ssl=False):
        if ssl:
            bottle_port = 4443
            websocket_port = 9999
        else:
            bottle_port = 4442
            websocket_port = 4444
        # start bottle server
        self.rack_server.bottle_server_add(port=bottle_port)
        # start gedis websocket
        gedis_websocket_server = j.servers.gedis_websocket.default.app
        self.rack_server.websocket_server_add("websocket", websocket_port, gedis_websocket_server)

        if ssl:
            # create reverse proxies for websocket and bottle
            self._proxy_create("bottle_proxy", 4442, 4443)
            self._proxy_create("gedis_proxy", 4444, 9999, ptype="websocket")
            self._proxy_create("openresty", 443, 80)

    def start(self, background=False, web=None, ssl=None):
        """

        kosmos 'j.servers.threebot.default.start(background=True,web=False)'
        kosmos 'j.servers.threebot.default.start(background=False,web=False)'

        :param background: if True will start all servers including threebot itself in the background

        Threebot will start the following servers by default

        zdb                                         (port:9900)
        sonic                                       (port:1491)
        gedis                                       (port:8901)

        if web:
            openresty                                   (port:80 and 443 for ssl)
            gedis websocket                             (port:4444 or 9999 if ssl=True)
            bottle server                               (port:44442 or 4443 if ssl=True) serves the bcdbfs content

            if ssl=True:
                reverse proxy for gedis websocket           (port:4444) to use ssl certificate from openresty
                reverse proxy for bottle server             (port:4442) to use ssl certificate from openresty
        """
        if web is None:
            web = self.web

        if ssl is None:
            ssl = self.ssl

        if not background:
            if web:
                self._init_web(ssl=ssl)

            self.zdb.start()
            j.servers.sonic.default.start()

            # add system actors and basic chat flows
            self.gedis_server.actors_add("%s/base_actors" % self._dirpath)
            self.gedis_server.chatbot.chatflows_load("%s/base_chatflows" % self._dirpath)
            self.rack_server.add("gedis", self.gedis_server.gevent_server)

            bcdb = j.data.bcdb.system
            redis_server = bcdb.redis_server_get(port=6380, secret="123456")
            self.rack_server.add("bcdb_system_redis", redis_server.gevent_server)

            # add user added packages
            for package in j.tools.threebot_packages.find():
                try:
                    package.start()
                except Exception as e:
                    logdict = j.core.tools.log(level=50, exception=e, stdout=True)

            if web:
                self.openresty_server.start()
            self.rack_server.start()

        else:
            if self.startup_cmd.is_running():
                self.startup_cmd.stop()
            self.startup_cmd.start()

    def stop(self):
        """
        :return:
        """
        self.startup_cmd.stop(waitstop=False, force=True)

    @property
    def startup_cmd(self):
        if not self._startup_cmd:
            cmd_start = """
            from gevent import monkey
            monkey.patch_all(subprocess=False)
            from Jumpscale import j
            server = j.servers.threebot.get("{name}", executor='{executor}', web={web}, ssl={ssl})
            server.start(background=False)
            """.format(
                name=self.name, executor=self.executor, web=self.web, ssl=self.ssl
            )
            cmd_start = j.core.tools.text_strip(cmd_start)
            startup = j.servers.startupcmd.get(name="threebot_{}".format(self.name), cmd_start=cmd_start)
            startup.executor = self.executor
            startup.interpreter = "python"
            startup.timeout = 60
            startup.ports = [8901, 4444, 8090]
            self._startup_cmd = startup
        return self._startup_cmd
