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
        name* = "main" (S)
        executor = tmux,corex (E)
        adminsecret_ = "123456"  (S)
        """

    def _init(self, **kwargs):
        self._rack_server = None
        self._gedis_server = None
        self._openresty_server = None
        self._startup_cmd = None
        self._zdb = None
        self.threebot_server = None
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
        return self._openresty_server

    def bcdb_get(self, name):
        if j.data.bcdb.exists(name=name):
            return j.data.bcdb.get(name=name)
        else:
            zdb_admin = j.clients.zdb.client_admin_get()
            zdb = zdb_admin.namespace_new(name, secret=self.secret)
            return j.data.bcdb.new(name=name, storclient=zdb)

    @property
    def zdb(self):
        if not self._zdb:
            self._zdb = j.servers.zdb.get(
                name=f"{self.name}_zdb_threebot", adminsecret_=self.adminsecret_, executor=self.executor
            )
        return self._zdb

    def start(self, background=False, web=False):
        """

        kosmos 'j.servers.threebot.default.start(background=True,web=False)'
        kosmos 'j.servers.threebot.default.start(background=False,web=False)'

        :param background: if True will start all servers including threebot itself in the background

        Threebot will start the following servers by default

        zdb                                         (port:9900)
        sonic                                       (port:1491)
        gedis                                       (port:8901)
        openresty                                   (port:80 and 443 for ssl)
        gedis websocket                             (port:9999)
        reverse proxy for gedis websocket           (port:4444) to use ssl certificate from openresty
        dns server                                  (port:5354) #TODO: check if this is still needed
        bottle server                               (port:4443) serves the bcdbfs content
        reverse proxy for bottle server             (port:4442) to use ssl certificate from openresty
        """

        if not background:

            if web:
                # starting servers
                self.openresty_server.install(reset=True)
            self.zdb.start()
            j.servers.sonic.default.start()

            # add system actors and basic chat flows
            self.gedis_server.actors_add("%s/base_actors" % self._dirpath)

            self.gedis_server.chatbot.chatflows_load("%s/base_chatflows" % self._dirpath)
            gedis_websocket_server = j.servers.gedis_websocket.default.app
            self.rack_server.websocket_server_add("websocket", 9999, gedis_websocket_server)

            if web:
                websocket_reverse_proxy = self.openresty_server.reverseproxies.get(
                    name=f"{self.name}_websocket_threebot",
                    port_source=4444,
                    proxy_type="websocket",
                    port_dest=9999,
                    ipaddr_dest="0.0.0.0",
                )
                websocket_reverse_proxy.configure()

            dns = j.servers.dns.get_gevent_server("main", port=5354)  # for now high port
            self.rack_server.add("dns", dns)

            self.rack_server.add("gedis", self.gedis_server.gevent_server)

            if web:
                gedis_reverse_proxy = self.openresty_server.reverseproxies.get(
                    name="gedis_websocket", port_source=8900, proxy_type="tcp", port_dest=8901, ipaddr_dest="0.0.0.0"
                )

                gedis_reverse_proxy.configure()

            self.rack_server.bottle_server_add(port=4443)

            if web:
                bottle_reverse_proxy = self.openresty_server.reverseproxies.get(
                    name="bottle_websocket", port_source=4442, proxy_type="http", port_dest=4443, ipaddr_dest="0.0.0.0"
                )

                bottle_reverse_proxy.configure()

            # add user added packages
            for package in j.tools.threebot_packages.find():
                package.start()

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
            server = j.servers.threebot.get("{name}", executor='{executor}')
            server.start(background=False)
            """.format(
                name=self.name, executor=self.executor
            )
            cmd_start = j.core.tools.text_strip(cmd_start)
            startup = j.servers.startupcmd.get(name="threebot_{}".format(self.name), cmd_start=cmd_start)
            startup.executor = self.executor
            startup.interpreter = "python"
            startup.timeout = 60
            startup.ports = [8900, 4444, 8090]
            self._startup_cmd = startup
        return self._startup_cmd

    # def auto_update(self):
    #     while True:
    #         self._log_info("Reload for docsites done")
    #         gevent.sleep(300)
