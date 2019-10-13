from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest


class TestOdooServer(BaseTest):
    def setUp(self):
        self.info("​Install odoo server , and get new instance of it ")
        j.servers.odoo.install()
        self.odoo_server = j.servers.odoo.get()
        self.odoo_server.start()

    def Teardown(self):
        self.info(" Stop odoo server.")
        self.odoo_server.stop()

    def test01_create_database(self):
        """
        - ​Install and start odoo server , and get new instance of it . 
        - Create new database.
        - Check that created database exist in databases_list.
        - Check that new data base created successfully.
        - stop odoo server.
        """
        self.info("Create new database ")
        database = self.odoo_server.databases.new()
        self.set_database_data(database)
        self.odoo_server.databases_create()
        self.odoo_server.save()

        self.info("Check that created database exist in databases_list.")
        databases = self.odoo_server.databases_list()
        self.assertIn(database.name, databases)

        self.info("Check that new database created successfully.")
        database_client = self.odoo_server.client_get(database.name)
        user_name = self.rand_string()
        user_password = self.rand_string()
        database_client.user_add(user_name, user_password)
        database_client.login(user_name, user_password)
        wrong_passsword = self.rand_string()
        with self.assertRaises(Exception):
            database_client.login(user_name, wrong_passsword)

        database_client.user_delete(user_name, user_password)
        with self.assertRaises(Exception):
            database_client.login(user_name, user_password)

        self.info(" stop odoo server.")
        self.odoo_server.stop()

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test02_create_databases(self):
        """
        - ​Install and start odoo server , and get new instance of it . 
        - Create database [db1].
        - Create second database [db2] with reset=false, should create another database only..
        - Create another database [db3] with reset =true, should delete all old databases and create another one.
        """
        self.info("Create database [db1].")
        db1 = self.odoo_server.databases.new()
        self.set_database_data(db1)
        self.odoo_server.databases_create()
        self.odoo_server.save()

        self.info("Create second database [db2] with reset=false, should create another database only.")
        db2 = self.odoo_server.databases.new()
        self.set_database_data(db2)
        self.odoo_server.databases_create(reset=False)
        self.odoo_server.save()
        self.assertIn(db1.name, self.odoo_server.databases_list())
        self.assertIn(db2.name, self.odoo_server.databases_list())

        self.info(
            "Create another database [db3] with reset =true, should delete all old databases and create another one."
        )
        db3 = self.odoo_server.databases.new()
        self.set_database_data(db3)
        self.odoo_server.databases_create(reset=True)
        self.odoo_server.save()
        self.assertNotIn(db1.name, self.odoo_server.databases_list())
        self.assertNotIn(db2.name, self.odoo_server.databases_list())
        self.assertIn(db3.name, self.odoo_server.databases_list())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test03_reset_databases(self):
        """
        - ​Install and start odoo server , and get new instance of it . 
        - Try reset_database, should delete all databases.
        """
        self.info("Create database.")
        db = self.odoo_server.databases.new()
        self.set_database_data(db)
        self.odoo_server.databases_create()
        self.odoo_server.save()

        self.info("Try reset_database, should delete all databases.")
        self.odoo_server.databases_reset()
        self.assertFalse(self.odoo_server.databases_list())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test04_export_import_databases(self):
        """
        - ​Install and start odoo server , and get new instance of it . 
        - Export created database, check that zip file exist.
        - Import database, check that imported database exist in database list
        """
        self.info("Create database.")
        db = self.odoo_server.databases.new()
        self.set_database_data(db)
        self.odoo_server.databases_create()
        self.odoo_server.save()

        self.info("Export created database, check that zip file exist.")
        export_dir = "/root/exports/"
        output, error = self.os_command("mkdir {}".format(export_dir))
        self.odoo_server.database_export(db.name, export_dir)
        output, error = self.os_command(" ls /root/exports")
        self.assertIn("{}.zip".format(db.name), output.decode())

        self.info("Import database, check that imported database exist in database list")
        self.odoo_server.databases_reset()
        self.odoo_server.database_import(db.name, export_dir)
        self.assertIn(db.name, self.odoo_server.databases_list())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test05_write_and_read(self):
        """
        - ​Install and start odoo server , and get new instance of it .
        - Create database [db].
        - Wrtie data[dt] in [db], check that it writes successfully.
        - Export data [dt].
        - Import data [dt].
        - Read data [dt] from db [db].
        - Delete data [dt], check it deleted successfully.
        """
        pass
