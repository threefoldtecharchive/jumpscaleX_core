from Jumpscale import j
from .ZDBServer import ZDBServer

JSConfigs = j.baseclasses.object_config_collection_testtools
TESTTOOLS = j.baseclasses.testtools


class ZDBServers(JSConfigs, TESTTOOLS):
    """
    Open Publish factory
    """

    __jslocation__ = "j.servers.zdb"
    _CHILDCLASS = ZDBServer

    def _init(self, **kwargs):
        self._default = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get(name="default")
        return self._default

    def install(self, reset=True):
        """
        kosmos 'j.servers.zdb.install()'
        """
        j.builders.db.zdb.install(reset=reset)

    def test_instance_start(
        self, destroydata=False, namespaces=None, admin_secret=None, namespaces_secret="1234", restart=False
    ):
        """

        kosmos 'j.servers.zdb.test_instance_start()'

        start a test instance with j.core.myenv.adminsecret
        will use port 9901
        and name = test_instance

        production is using other ports and other secret

        :return:
        """
        if not namespaces:
            namespaces = []
        zdb = self.get(name="test_instance", port=9901, autosave=True)

        if destroydata:
            zdb.destroy()
            j.clients.redis._cache_clear()  # make sure all redis connections gone

        zdb.start()
        # zdb.save()  #no longer needed happens auto

        cla = zdb.client_admin_get()

        for ns in namespaces:
            if not cla.namespace_exists(ns):
                cla.namespace_new(ns, secret=namespaces_secret)
            else:
                if destroydata:
                    cla.namespace_delete(ns)
                    cla.namespace_new(ns, secret=namespaces_secret)

        if destroydata:
            j.clients.redis._cache_clear()  # make sure all redis connections gone

        return zdb

    def test_instance_stop(self, destroy=True):
        zdb = self.get(name="test_instance", port=9901)
        zdb.stop()
        if destroy:
            zdb.destroy()
            zdb.delete()

    def test(self, name="", install=False):
        """
        kosmos 'j.servers.zdb.test(build=True)'
        kosmos 'j.servers.zdb.test()'
        """

        if install:
            self.install()

        self._tests_run(name=name)
        print("TEST OK")
