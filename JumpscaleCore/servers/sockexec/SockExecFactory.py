from Jumpscale import j
from .SockExec import SockExec


class SockExecFactory(j.baseclasses.object_config_collection_testtools):
    """
    SockExec factory
    """

    __jslocation__ = "j.servers.sockexec"
    _CHILDCLASS = SockExec

    def _init(self, **kwargs):
        self._default = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get(name="default")
        return self._default
