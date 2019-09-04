from Jumpscale import j

from .WireGuard import WireGuard


class WGFactory(j.baseclasses.object_config_collection_testtools):
    """
    wireguard factory

    works over ssh

    """

    __jslocation__ = "j.tools.wireguard"
    _CHILDCLASS = WireGuard

    def get_by_id(self, id):
        data = self._model.get(id)
        return self._new(data.name, data)

    def test(self):
        """
        kosmos -p 'j.tools.wireguard.test()'
        :return:
        """
        # setup server on a digital ocean client
        print("Configuring server")
        wgs = self.get(name="test5", sshclient_name="do", network_private="10.5.0.1/24")
        wgs.sshclient_name = "do"
        wgs.interface_name = "wg-test"
        wgs.network_private = "10.5.0.1/24"
        wgs.network_public = wgs.executor.sshclient.addr
        wgs.save()

        # configure local client
        print("Configuring local client")
        wg = self.get(name="local", sshclient_name="myhost")
        wg.network_private = "10.5.0.2/24"
        wg.port = 7778
        wg.interface_name = "wg-test"
        wg.peer_add(wgs)
        wg.save()

        print("Adding client to server")
        wgs.peer_add(wg)
        wgs.save()

        print("Install server")
        wgs.install()
        wgs.configure()

        print("Install client")
        wg.install()
        wg.configure()
