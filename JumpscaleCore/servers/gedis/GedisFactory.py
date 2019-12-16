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

    def _cmds_get(self, key, data, package=None):
        """
        Used in client only, starts from data (python client)
        """
        name = key
        return GedisCmds(name=name, data=data, package=package)

    def test(self, name="basic"):
        """
        it's run all tests
        kosmos 'j.servers.gedis.test()'

        """
        # we don't support running gevent as stdallone any longer

        if not j.sal.nettools.tcpPortConnectionTest("localhost", 8901):
            # make sure we have a threebot life
            cl = j.servers.threebot.local_start_default()
        else:
            cl = j.clients.gedis.get(name="test", port=8901)

        cl_pm = j.clients.gedis.get(name="packagemanager", port=8901, package_name="zerobot.packagemanager")
        cl_pm.actors.package_manager.package_add(
            git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/development_actorsimprovement/ThreeBotPackages/tfgrid/phonebook"
        )

        self._threebot_client_default = cl
        self._threebot_client_default_packagemanager = cl_pm

        self._test_run(name=name)
