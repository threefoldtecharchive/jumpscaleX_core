from Jumpscale import j
from .LoggerClient import LoggerClient


class LoggerFactory(j.baseclasses.object_config_collection_testtools):

    __jslocation__ = "j.clients.logger"
    _CHILDCLASS = LoggerClient

    def _init(self, **kwargs):
        self._core = None

    @property
    def core(self):
        if not self._core:
            self._core = self.get(name="core")
        return self._core

    def test(self, name="base"):
        """
        kosmos 'j.clients.logger.test()'
        """
        self._tests_run(name=name)
