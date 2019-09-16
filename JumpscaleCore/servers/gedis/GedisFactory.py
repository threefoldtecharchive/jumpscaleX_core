import os

from Jumpscale import j

from .GedisServer import GedisServer
from .GedisCmds import GedisCmds
from .GedisChatBot import GedisChatBotFactory


class GedisFactory(j.baseclasses.object_config_collection, j.baseclasses.testtools):
    __jslocation__ = "j.servers.gedis"
    _CHILDCLASS = GedisServer

    def get_gevent_server(self, name="", **kwargs):
        """
        return gedis_server as gevent server

        j.servers.gedis.get("test")


        """
        server = self.get(name=name, **kwargs)

        return server.gevent_server

    def _cmds_get(self, key, data):
        """
        Used in client only, starts from data (python client)
        """
        namespace, name = key.split("__")
        return GedisCmds(namespace=namespace, name=name, data=data)

    def test(self, name="basic"):
        """
        it's run all tests
        kosmos 'j.servers.gedis.test()'

        """
        # we don't support running gevent as stdallone any longer
        self.client = j.threebot.package.ibiza.client_get()

        self._test_run(name=name)
