from Jumpscale import j
from base_test import BaseTest
from parameterized import parameterized
import random, uuid, requests
from requests import ConnectionError


class TestServers(BaseTest):
    def setUp(self):
        pass

    @parameterized.expand(BaseTest.SERVERS.keys())
    def Test01_install_option(self, server):
        """
        - ​​​​​Install server . 
        - Make sure that server installed successfully.

        """
        if "install" not in BaseTest.SERVERS[server].keys():
            pass
        self.info("Install Server {}".format(server))
        getattr(j.servers, server).install()

        self.info("Make sure that server installed successfully.")
        output, error = self.os_command("{} --help".format(server))
        self.assertIn(BaseTest.SERVERS[server]["install"], output.decode())

    @parameterized.expand(BaseTest.SERVERS.keys())
    def Test02_start_stop_options(self, server):
        """
        - Start server . 
        - Make sure that server started successfully.
        - Check that server connection  works successfully.
        - Stop server
        - Check that can't connect to server anymore.
        """
        if "start" not in BaseTest.SERVERS[server].keys():
            pass
        self.info("Start Server {}".format(server))
        server = getattr(j.servers, server).get()
        server.start()
        self.info("Make sure that server started successfully.")
        output, error = self.os_command("ps -aux | grep {}".format(server))
        self.assertTrue(output.decode())

        self.info("Check that server connection  works successfully.")
        response = requests.get("http://127.0.0.1:{}".format(server.port))
        self.assertEqual(response.status_code, 200)

        self.info("Stop server {}".format(server))
        server.stop()
        output, error = self.os_command("ps -aux | grep {}".format(server))
        self.assertFalse(output.decode())

        self.info("Check that can't connect to server anymore.")
        try:
            response = requests.get("http://127.0.0.1:{}".format(server.port))
            self.assertNotEqual(response.status_code, 200)
        except ConnectionError as e:
            self.assertIn("Failed to establish a new connection", e)

    @parameterized.expand(BaseTest.SERVERS.keys())
    def Test03_port_and_name_options(self, server):
        """
        - install server with default port and get server.
        - Make sure that server started successfully.

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
