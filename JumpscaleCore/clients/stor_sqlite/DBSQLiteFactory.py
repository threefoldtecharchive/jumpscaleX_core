from Jumpscale import j

from .DBSQLite import DBSQLite


# DO NOT USE CONFIG OBJECT HERE, OTHERWISE CHICKEN AND EGG SITUATION
class DBSQLiteFactory(j.baseclasses.object, j.baseclasses.testtools):
    __jslocation__ = "j.clients.sqlitedb"

    def client_get(self, namespace, fromcache=True, readonly=False):
        """
        :param nsname: namespace name
        :return:
        """
        return DBSQLite(nsname=namespace, readonly=readonly)

    def test(self):
        """
        kosmos 'j.clients.sqlitedb.test()'

        """

        self._test_run(name="base")
