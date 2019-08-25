from Jumpscale import j
import os
import gevent
from .OpenPublish import OpenPublish

JSConfigs = j.baseclasses.factory


class BCDBs:
    def __init__(self):
        pass


class ThreeBotServer(j.baseclasses.object_config):
    """
    Open Publish factory
    """

    _SCHEMATEXT = """
        @url = jumpscale.threebotserver.1
        name* = "main" (S)
        executor = tmux,corex (E)
        adminsecret_ = "123456"  (S)
        """

    def _init(self, **kwargs):
        self.content = ""
        self._rack = None
        self._gedis_server = None
        self._startup_cmd = None
        self._openresty = None

        self.bcdbs = BCDBs()
        j.servers.threebot.current = self

    @property
    def secret(self):
        return self.adminsecret_

    @property
    def rack(self):
        if not self._rack:
            self._rack = j.servers.rack.get()
        return self._rack

    def bcdb_get(self, name):
        if not name in self.bcdbs__dict__:
            # will be made more secure but for now ok
            zdb_admin = j.clients.zdb.client_admin_get()
            name = "wiki"
            if not j.data.bcdb.exists(name=name):
                zdb = zdb_admin.namespace_new(name, secret=self.secret)
                bcdb = j.data.bcdb.new(name=name, storclient=zdb)
            else:
                bcdb = j.data.bcdb.get(name=name)
            self.bcdbs__dict__[name] = bcdb
        return self.bcdbs__dict__[name]

    @property
    def gedis_server(self):
        if not self._gedis_server:
            self._gedis_server = j.servers.gedis.get("threebot_%s" % self.name, port=8901)
        return self._gedis_server

    @property
    def openresty(self):
        if not self._openresty:
            self._openresty = j.servers.openresty.get("threebot", executor=self.executor)
        return self._openresty

    def start(self, background=False):
        """

        kosmos 'j.servers.threebot.default.start()'

        :param background:
        :return:
        """

        if not background:

            j.application.debug = False  # otherwise we get a pudb session

            zdb = j.servers.zdb.get("threebot", adminsecret_=self.adminsecret_, executor=self.executor)
            zdb.start()

            self.openresty = j.servers.openresty.get("threebot", executor=self.executor)
            self.openresty.install()

            j.servers.sonic.default.start()

            # add system actors
            self.gedis_server.actors_add("%s/base_actors" % self._dirpath)
            self.gedis_server.chatbot.chatflows_load("%s/base_chatflows" % self._dirpath)

            app = j.servers.gedis_websocket.default.app
            self.rack.websocket_server_add("websocket", 9999, app)

            websocket_reverse_proxy = self.openresty.reverseproxies.new(
                name="websocket", port_source=4444, proxy_type="websocket", port_dest=9999, ipaddr_dest="0.0.0.0"
            )

            websocket_reverse_proxy.configure()

            dns = j.servers.dns.get_gevent_server("main", port=5354)  # for now high port
            self.rack.add("dns", dns)

            self.rack.add("gedis", self.gedis_server.gevent_server)

            gedis_reverse_proxy = self.openresty.reverseproxies.new(
                name="gedis", port_source=8900, proxy_type="tcp", port_dest=8901, ipaddr_dest="0.0.0.0"
            )

            gedis_reverse_proxy.configure()

            self.rack.bottle_server_add(port=4443)

            bottle_reverse_proxy = self.openresty.reverseproxies.new(
                name="bottle", port_source=4442, proxy_type="http", port_dest=4443, ipaddr_dest="0.0.0.0"
            )

            bottle_reverse_proxy.configure()

            # add user added packages
            for package in j.tools.threebotpackage.find():
                package.start()

            self.openresty.start()
            self.rack.start()

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
