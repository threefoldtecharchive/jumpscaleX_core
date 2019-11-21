from Jumpscale import j


class GridnetworkFactory(j.baseclasses.object):
    __jslocation__ = "j.clients.gridnetwork"

    def get(self, gedisclient_name):
        gedisclient = j.clients.gedis.get(gedisclient_name)
        return GridnetworkClient(gedisclient)


class GridnetworkClient(j.baseclasses.object):
    def __init__(self, gedisclient):
        self._gedisclient = gedisclient
        self._network = self._gedisclient.actors.gridnetwork

    def networks_find(self):
        return self._network.networks_find()

    def network_connect(self, networkname, doublename=None, sshclient_name=None, port=7777, interface_name="wg0"):
        wg = j.tools.wireguard.get(f"{networkname}_{sshclient_name}", autosave=False)
        wg.sshclient_name = sshclient_name
        try:
            wg.install()
        except:
            wg.delete()
            raise
        wg.key_pair_get()
        wg.port = port
        wg.interface_name = interface_name

        uniquename = doublename or wg.executor.platformtype.hostname
        serverinfo = self._network.network_peer_add(networkname, uniquename, wg.key_public)
        wg.network_private = serverinfo.network_private
        for endpoint in serverinfo.endpoints:
            # save local copy of endpoint
            localendpoint = j.tools.wireguard.get(f"{endpoint.network_public}:{endpoint.port}")
            localendpoint.port = endpoint.port
            localendpoint.key_public = endpoint.key_public
            localendpoint.network_public = endpoint.network_public
            localendpoint.network_private = endpoint.network_private
            localendpoint.save()

            wg.peer_add(localendpoint)

        wg.save()
        try:
            wg.configure()
        except:
            wg.delete()
            self._network.network_peer_remove(networkname, uniquename)
            raise

        return wg
