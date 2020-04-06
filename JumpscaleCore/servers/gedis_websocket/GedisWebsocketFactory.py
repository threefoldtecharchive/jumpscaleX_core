import socket
from Jumpscale import j

from .GedisWebsocketServer import GedisWebsocketServer

JSConfigClient = j.baseclasses.object_config_collection

skip = j.baseclasses.testtools._skip


class GedisWebsocketFactory(JSConfigClient):
    __jslocation__ = "j.servers.gedis_websocket"
    _CHILDCLASS = GedisWebsocketServer

    def _init(self, **kwargs):
        self._default = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get("default")
        return self._default

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/575")
    def test(self):
        """
        kosmos 'j.servers.gedis_websocket.test()'
        """
        j.servers.threebot.default.start(background=True)
        self.client_gedis = j.clients.gedis.get("test_gedis", port=8901, package_name="zerobot.webinterface")
        self.client_gedis.actors.chatbot.ping()
        return "DONE"
