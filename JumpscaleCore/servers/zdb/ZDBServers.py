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

    def install(self, reset=False):
        """
        kosmos 'j.servers.zdb.install()'
        """
        j.builders.db.zdb.install(reset=reset)

    def test_instance_start(self, namespaces=["test"], admin_secret="123456", namespaces_secret="1234", restart=False):
        """

        kosmos 'j.servers.zdb.test_instance_start()'

        start a test instance with self.adminsecret 123456
        will use port 9901
        and name = test_instance

        production is using other ports and other secret

        :return:
        """
        if not namespaces:
            namespaces = []
        j.servers.zdb.install()
        zdb = self.get(name="testserver", port=9901, autosave=True, adminsecret_=admin_secret)

        if restart:
            zdb.destroy()
            j.clients.redis._cache_clear()  # make sure all redis connections gone

        zdb.start()

        cla = zdb.client_admin_get()

        for ns in namespaces:
            if cla.namespace_exists(ns):
                cla.namespace_delete(ns)
            cla.namespace_new(ns, secret=namespaces_secret)
            cl = zdb.client_get(nsname=ns, secret=namespaces_secret)

        j.clients.redis._cache_clear()  # make sure all redis connections gone

        # check zdb server is running & data dir does exist
        j.clients.zdb.testserver_admin.ping()  # some extra tests, lets leave for now
        j.clients.zdb.testserver.ping()
        assert zdb.isrunning() == True

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
