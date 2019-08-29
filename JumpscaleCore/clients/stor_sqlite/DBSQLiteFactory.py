from Jumpscale import j

from .DBSQLite import DBSQLite


class DBSQLiteFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.sqlitedb"
    _CHILDCLASS = DBSQLite

    def client_get(self, namespace, fromcache=True):
        """
        :param nsname: namespace name
        :return:
        """
        return DBSQLite(nsname=namespace)

    def test(self):
        """
        kosmos 'j.clients.sqlitedb.test()'

        """

        self._test_run(name="base")
