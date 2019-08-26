import os

from Jumpscale import j

from .GedisServer import GedisServer
from .GedisCmds import GedisCmds
from .GedisChatBot import GedisChatBotFactory

JSConfigFactory = j.baseclasses.object_config_collection


class GedisFactory(JSConfigFactory):
    __jslocation__ = "j.servers.gedis"
    _CHILDCLASS = GedisServer

    def get_gevent_server(self, name="", **kwargs):
        """
        return gedis_server as gevent server

        j.servers.gedis.get("test")


        """
        self.new(name=name, **kwargs)
        server = self.get(name=name)

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
        j.servers.rack._server_test_start()  # makes sure we have a gevent serverrack which runs a gevent service
        # now can run the rest of the tests

        self._test_run(name=name)
