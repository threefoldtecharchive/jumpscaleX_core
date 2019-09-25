from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest


class TestOdooServer(BaseTest):
    def setUp(self):
        pass

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test01_create_database(self):
        """
        - ​Install and start odoo server , and get new instance of it . 
        - Create new database.
        - Check that created database exist in databases_list.
        - Check that new data base created successfully.
        - Teardown odoo server.
        """
        self.info("​Install odoo server , and get new instance of it ")
        j.servers.odoo.install()
        odoo_server = j.servers.odoo.get()
        odoo_server.start()

        self.info("Create new database ")
        database = odoo_server.databases.new()
        self.set_database_data(database)
        odoo_server.databases_create()
        odoo_server.save()

        self.info("Check that created database exist in databases_list.")
        databases = odoo_server.databases_list()
        self.assertIn(database.name, databases)

        self.info("Check that new database created successfully.")
        database_client = odoo_server.get_client(database.name)
        user_name = str(uuid.uuid4()).replace("-", "")[1:10]
        user_password = str(uuid.uuid4()).replace("-", "")[1:10]
        database_client.user_add(user_name, user_password)
        database_client.login(user_name, user_password)
        wrong_passsword = str(uuid.uuid4()).replace("-", "")[1:10]
        with self.assertRaises(Exception):
            database_client.login(user_name, wrong_passsword)

        database_client.user_delete(user_name, user_password)
        with self.assertRaises(Exception):
            database_client.login(user_name, user_password)

        self.info(" Teardown odoo server.")
        odoo_server.stop()

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test02_create_databases(self):
        """
        - ​Install and start odoo server , and get new instance of it . 
        - Create database [db1].
        - Create second database [db2] with reset=false, should create another database only..
        - Create another database [db3] with reset =true, should delete all old databases and create another one.
        """
        self.info("​Install odoo server , and get new instance of it ")
        j.servers.odoo.install()
        odoo_server = j.servers.odoo.get()
        odoo_server.start()

        self.info("Create database [db1].")
        db1 = odoo_server.databases.new()
        self.set_database_data(db1)
        odoo_server.databases_create()
        odoo_server.save()

        self.info("Create second database [db2] with reset=false, should create another database only.")
        db2 = odoo_server.databases.new()
        self.set_database_data(db2)
        odoo_server.databases_create(reset=False)
        odoo_server.save()
        self.assertIn(db1.name, odoo_server.databases_list())
        self.assertIn(db2.name, odoo_server.databases_list())

        self.info(
            "Create another database [db3] with reset =true, should delete all old databases and create another one."
        )
        db3 = odoo_server.databases.new()
        self.set_database_data(db3)
        odoo_server.databases_create(reset=True)
        odoo_server.save()
        self.assertNotIn(db1.name, odoo_server.databases_list())
        self.assertNotIn(db2.name, odoo_server.databases_list())
        self.assertIn(db3.name, odoo_server.databases_list())

        self.info(" Teardown odoo server.")
        odoo_server.stop()

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test03_reset_databases(self):
        """
        - ​Install and start odoo server , and get new instance of it . 
        - Try reset_database, should delete all databases.
        """

        self.info("​Install odoo server , and get new instance of it ")
        j.servers.odoo.install()
        odoo_server = j.servers.odoo.get()
        odoo_server.start()

        self.info("Create database.")
        db = odoo_server.databases.new()
        self.set_database_data(db)
        odoo_server.databases_create()
        odoo_server.save()

        self.info("Try reset_database, should delete all databases.")
        odoo_server.databases_reset()
        self.assertFalse(odoo_server.databases_list())

        self.info(" Teardown odoo server.")
        odoo_server.stop()

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test04_export_import_databases(self):
        """
        - ​Install and start odoo server , and get new instance of it . 
        - Export created database, check that zip file exist.
        - Import database, check that imported database exist in database list
        """

        self.info("​Install odoo server , and get new instance of it ")
        j.servers.odoo.install()
        odoo_server = j.servers.odoo.get()
        odoo_server.start()

        self.info("Create database.")
        db = odoo_server.databases.new()
        self.set_database_data(db)
        odoo_server.databases_create()
        odoo_server.save()

        self.info("Export created database, check that zip file exist.")
        export_dir = "/root/exports"
        export_dest = self.os_command("mkdir {}".format(export_dir))
        odoo_server.database_export(db.name, export_dir)
        output, error = self.os_command(" ls /root/exports")
        self.assertIn("{}.zip".format(db.name), output.decode())

        self.info("Import database, check that imported database exist in database list")
        odoo_server.databases_reset()
        database_name = str(uuid.uuid4()).replace("-", "")[1:10]
        odoo_server.database_import(database_name, export_dir)
        self.assertIn(database_name, odoo_server.databases_list())

        self.info(" Teardown odoo server.")
        odoo_server.stop()

    # def test05_write_and_read(self):
    #     """
    #     - ​Install and start odoo server , and get new instance of it .
    #     - Create database [db].
    #     - Wrtie data[dt] in [db], check that it writes successfully.
    #     - Export data [dt].
    #     - Import data [dt].
    #     - Read data [dt] from db [db].
    #     - Delete data [dt], check it deleted successfully.
