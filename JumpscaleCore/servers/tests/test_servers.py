from Jumpscale import j
from base_test import BaseTest
from parameterized import parameterized
import random, requests, uuid, unittest
from requests import ConnectionError


class TestServers(BaseTest):
    def setUp(self):
        pass

    @parameterized.expand(BaseTest.SERVERS)
    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/30")
    def Test01_install_option(self, server):
        """
        - ​​​​​Install server . 
        - Make sure that server installed successfully.

        """
        self.info("Install Server {}".format(server))
        getattr(j.servers, server).install()

        self.info("Make sure that server installed successfully.")
        output, error = self.os_command("{} --help".format(server))
        self.assertIn("USAGE", output.decode())

    @parameterized.expand(BaseTest.SERVERS)
    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/30")
    def Test02_start_stop_options(self, server):
        """
        - Start server. 
        - Make sure that server started successfully.   
        - Check that server connection  works successfully.
        - Stop server
        - Check that can't connect to server anymore.
        """
        self.info("* Start Server {}".format(server))
        server = getattr(j.servers, server).get()
        if server in ["threebot"]:
            server.start(background=True)
        else:
            server.start()

        self.info(" * Make sure that server started successfully.")
        output, error = self.os_command(" ps -aux | grep -v grep | grep {} | awk '{print $2}'".format(server))
        self.assertTrue(output.decode())

        self.info(" * Check that server connection  works successfully.")
        server_PID = output.decode()
        output, error = self.os_command("netstat -nltp | grep ':{}' ".format(server_PID))
        self.assertTrue(output)

        self.info(" * Stop server {}".format(server))
        server.stop()
        output, error = self.os_command("ps -aux | grep -v grep | grep {} | awk '{print $2}'".format(server))
        self.assertFalse(output.decode())

        self.info("* Check that can't connect to server anymore.")
        output, error = self.os_command("netstat -nltp | grep ':{}' ".format(server_PID))
        self.assertFalse(output)

    @parameterized.expand(BaseTest.SERVERS)
    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/30")
    def Test03_port_and_name_options(self, server):
        """
        - install server with default port and get server.
        - Make sure that server started successfully.
        - Teardown the server.
        """
        self.info("Install server with default port and get server.")
        getattr(j.servers, server).install()
        server = getattr(j.servers, server).get()

        self.info("Change server port and name. ")
        new_port = random.randint(2000, 3000)
        new_name = str(uuid.uuid4()).replace("-", "")[1:10]
        server.port = new_port
        server.name = new_name

        self.info("​​​​​Start the server and check the  port server started with")
        server.start()
        output, error = self.os_command("ps -aux | grep {}".format(server))
        self.assertIn(new_port, output.decode())
        self.assertIn(new_name, output.decode())
        self.info(" Teardown the server.")
        server.stop()

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test04_odoo_create_database(self):
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
    def test05_odoo_create_databases(self):
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
    def test06_odoo_reset_databases(self):
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
    def test07_odoo_export_import_databases(self):
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
        odoo_server.database_export(db.name, export_dest)
        output, error = self.os_command(" ls /root/exports")
        self.assertIn("{}.zip".format(db.name), output.decode())

        self.info("Import database, check that imported database exist in database list")
        odoo_server.databases_reset()
        database_name = str(uuid.uuid4()).replace("-", "")[1:10]
        odoo_server.database_import(database_name, export_dest)
        self.assertIn(database_name, odoo_server.databases_list())

        self.info(" Teardown odoo server.")
        odoo_server.stop()

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/93")
    def test08_tmux_create_new_session(self):
        """
        - ​Install tmux server.
        - Create new session.
        - Check that created session exist session list.
        - Check that tmux session opened with right name.
        """

        self.info("​Install tmux server.")
        j.servers.tmux.install()

        self.info("Create new session.")
        session_name = str(uuid.uuid4()).replace("-", "")[1:10]
        j.servers.tmux.server.new_session(session_name)

        self.info("Check that created session exist session list.")
        sessions_list = j.servers.tmux.server.list_sessions()
        self.assertIn(session_name, sessions_list)

        self.info("Check that tmux session opened with right name.")
        output, error = self.os_command("tmux ls")
        self.assertIn(session_name, output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/93")
    def test09_tmux_kill_session(self):
        """
        - ​Install tmux server.
        - Create new session.
        - Kill created session.
        - Check that tmux session deleted successfully.
        """

        self.info("​Install tmux server.")
        j.servers.tmux.install()

        self.info("Create new session.")
        session_name = str(uuid.uuid4()).replace("-", "")[1:10]
        j.servers.tmux.server.new_session(session_name)

        self.info("Kill created session.")
        j.servers.tmux.server.kill_session(session_name)

        self.info("check that tmux session deleted successfully.")
        sessions_list = j.servers.tmux.server.list_sessions()
        self.assertNotIn(session_name, sessions_list)
        output, error = self.os_command("tmux ls")
        self.assertIn("no server running", output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/93")
    def test10_tmux_kill_server(self):
        """
        - ​Install tmux server.
        - Create two sessions.
        - Kill server.
        - Check that tmux server  and two sessions killed successfully.
        """

        self.info("​Install tmux server.")
        j.servers.tmux.install()

        self.info("Create two sessions.")
        session_name1 = str(uuid.uuid4()).replace("-", "")[1:10]
        session_name2 = str(uuid.uuid4()).replace("-", "")[1:10]
        j.servers.tmux.server.new_session(session_name1)
        j.servers.tmux.server.new_session(session_name2)

        self.info("Kill server.")
        j.servers.tmux.server.kill_server()

        self.info("check  that tmux server  and two sessions killed successfully .")
        sessions_list = j.servers.tmux.server.list_sessions()
        self.assertFalse(sessions_list)
        output, error = self.os_command("tmux ls")
        self.assertIn("no server running", output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/93")
    def test11_tmux_excute(self):
        """
        - Create new session.
        - Run server or process in created tmux session using execute.
        - Check that tmux session deleted successfully.
        """
        self.info("Create new session.")
        session_name = str(uuid.uuid4()).replace("-", "")[1:10]
        j.servers.tmux.server.new_session(session_name)
        sessions_list = j.servers.tmux.server.list_sessions()

        self.info("Run server or process in created tmux session using execute.")
        j.servers.tmux.execute("python -m SimpleHTTPServer", window=session_name)

        self.info("Check that tmux session deleted successfully.")
        output, error = self.os_command("ps -aux | grep -v grep | grep '{}'".format("python -m SimpleHTTPServer"))
        self.assertFalse(output.decode())
        self.assertEqual(sessions_list, j.servers.tmux.server.list_sessions())
        j.servers.tmux.server.kill_server()
