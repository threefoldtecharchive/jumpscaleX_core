from Jumpscale import j
from .TCPRouterClient import TCPRouterClient

JSConfigs = j.baseclasses.object_config_collection


class TCPRouterFactory(JSConfigs):

    __jslocation__ = "j.clients.tcp_router"
    _CHILDCLASS = TCPRouterClient

    def test(self):

        # get a client instance (TO CHECK: secret is already assigned to backend)
        cl = self.get("test_instance", local_address="0.0.0.0:18000", remote_address="127.0.0.1:6379", secret="test")

        # connect to backend
        cl.connect()

        # stop connection
        cl.stop()

        print("TEST OK")
