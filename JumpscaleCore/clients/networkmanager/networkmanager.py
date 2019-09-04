from Jumpscale import j

class NetManagerFactory:
    __jslocation__ = "j.clients.netmanager"

    def get(self, gedisclient_name):
        gedisclient = j.clients.gedis.get(gedisclient_name)
        return NetworkManagerClient(gedisclient)


class NetworkManagerClient:
    def __init__(self, gedisclient):
        self._gedisclient = gedisclient
        self._manager = self._gedisclient.actors.network_manager

    def networks_find(self):
        return self._manager.networks_find()

    def network_connect(self, networkname, sshclient_name=None, port=7777):
        wg = j.tools.wireguard.new(f"{networkname}_{sshclient_name}", save=False)
        wg.sshclient_name = sshclient_name
        try:
            wg.install()
        except:
            wg.delete()
            raise
        wg.key_pair_get()
        wg.port = port
        hostname = wg.executor.platformtype.hostname
        serverinfo = self._manager.network_peer_add(networkname, hostname, wg.key_public)
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
            self._manager.network_peer_remove(networkname, hostname)
            raise

