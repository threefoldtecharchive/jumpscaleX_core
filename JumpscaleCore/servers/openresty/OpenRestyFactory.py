from Jumpscale import j
import os


from .OpenRestyServer import OpenRestyServer

TESTTOOLS = j.baseclasses.testtools


class OpenRestyFactory(j.baseclasses.object_config_collection_testtools, TESTTOOLS):
    """
    Factory for openresty
    """

    __jslocation__ = "j.servers.openresty"
    _CHILDCLASS = OpenRestyServer

    def _init(self, **kwargs):
        self._default = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get(name="default")
        return self._default

    def install(self, reset=False):
        """
        kosmos 'j.servers.openresty.install(reset=True)'
        :param reset:
        :return:
        """
        if reset:
            j.sal.fs.remove(j.core.tools.text_replace("{DIR_BASE}/var/web"))
        j.builders.web.openresty.install()
        j.builders.runtimes.lua.install()
        j.builders.runtimes.lua.install_certificates()

    def test(self, name=None, install=True):
        """
        kosmos 'j.servers.openresty.test(install=False)'
        kosmos 'j.servers.openresty.test(name="basic")'
        :return:
        """
        if install:
            self.install()

        self._tests_run(name=name)
