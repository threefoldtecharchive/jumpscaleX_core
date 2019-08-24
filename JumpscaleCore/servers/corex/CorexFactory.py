from Jumpscale import j
from .CorexServer import CorexServer

JSConfigs = j.application.JSFactoryConfigsBaseClass


class CorexFactory(JSConfigs):
    """
    corex factory
    """

    __jslocation__ = "j.servers.corex"
    _CHILDCLASS = CorexServer

    def __init__(self):
        JSConfigs.__init__(self)
        self._default = None

    def install(self, reset=False):
        """
        kosmos 'j.servers.corex.install()'
        kosmos 'j.servers.corex.install(reset=True)'
        :return:
        """
        j.builders.apps.corex.install(reset=reset)

    @property
    def default(self):
        if not self._default:
            self._default = self.get("default")
        return self._default

    def test(self, reset=False):
        """
        kosmos 'j.servers.corex.test()'
        :return:
        """
        self.install(reset=reset)
        self.default.start()
        assert j.servers.startupcmd.corex_default.is_running()
        assert j.sal.nettools.tcpPortConnectionTest(ipaddr="localhost", port=1491)

        cl = j.clients.corex.get(name="test", addr="localhost", port=1491)

        self.default.stop()
        assert j.sal.nettools.tcpPortConnectionTest(ipaddr="localhost", port=1491) is False
