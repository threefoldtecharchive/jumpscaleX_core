from Jumpscale import j

from .DBSQLite import DBSQLite


# DO NOT USE CONFIG OBJECT HERE, OTHERWISE CHICKEN AND EGG SITUATION
class DBSQLiteFactory(j.baseclasses.object, j.baseclasses.testtools):
    __jslocation__ = "j.clients.sqlitedb"

    def client_get(self, bcdbname, fromcache=True, readonly=False):
        """
        :param bcdbname: bcdbname name
        :return:
        """
        return DBSQLite(bcdbname=bcdbname, readonly=readonly)

    def test(self):
        """
        kosmos 'j.clients.sqlitedb.test()'

        """

        self._tests_run(name="base")
