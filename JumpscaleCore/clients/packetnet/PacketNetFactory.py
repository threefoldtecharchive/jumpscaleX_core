from Jumpscale import j
from .PacketNet import PacketNet

JSConfigBaseFactory = j.baseclasses.object_config_collection


class PacketNetFactory(JSConfigBaseFactory):

    __jslocation__ = "j.clients.packetnet"
    _CHILDCLASS = PacketNet

    def _init(self, **kwargs):
        self.connections = {}

    def test(self):
        """
        do:
        kosmos 'j.clients.packetnet.test()'
        """
        client = self.get()
        self._log_debug(client.servers_list())

        # TODO:*1 connect to packet.net * boot zero-os
        # connect the client to zero-os
        # do a ping
