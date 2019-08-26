from Jumpscale import j

from .WGClient import WGClients
from .WGServer import WGServerFactory


class WGFactory(j.baseclasses.object_config_collection_testtools):
    """
    wireguard factory

    works over ssh

    """

    __jslocation__ = "j.tools.wireguard"
    _CHILDCLASS = WGServerFactory

    def test(self):
        """
        kosmos -p 'j.tools.wireguard.test()'
        :return:
        """
        wg = self.get(name="test", sshclient_name="do_gw9")
        wg.install()
        # wg.executor.installer.wireguard_go()

        j.shell()

        # get client linked to server
        cl = wg.clients.get(name="me")
        cl.install()

        j.shell()

        wg.configure()
        wg.start()

        j.shell()
