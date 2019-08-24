import socket
from Jumpscale import j

from .GedisWebsocketServer import GedisWebsocketServer

JSConfigClient = j.application.JSFactoryConfigsBaseClass


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

    def test(self):
        self.client_gedis = j.clients.gedis.get("main", port=8900)
        self.client_gedis.actors.chatbot.ping()
        return "DONE"
