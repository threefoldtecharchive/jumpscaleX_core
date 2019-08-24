from Jumpscale import j
from .MulticastClient import MulticastClient

JSConfigBase = j.application.JSFactoryConfigsBaseClass


class MulticastFactory(JSConfigBase):
    def __init__(self):
        self.__jslocation__ = "j.clients.multicast"
        JSConfigBase.__init__(self, MulticastClient)

    def test_listen(self):
        """
        js_shell 'j.clients.multicast.test_listen()'
        """
        data = {}
        # data["group"]='ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'
        data["port"] = 8123
        cl = self.get(data=data)
        print("listen")
        cl.listen()

    def test_send(self):
        """
        js_shell 'j.clients.multicast.test_send()'
        """
        data = {}
        data["group"] = "ff15:7079:7468:6f6e:6465:6d6f:6d63:6173"
        data["port"] = 8123
        cl = self.get(data=data)
        cl.send()
