from Jumpscale import j
from base_test import BaseTest
from parameterized import parameterized
import random, requests, uuid, unittest
from requests import ConnectionError


class TestServers(BaseTest):
    @classmethod
    def setUpClass(cls):

        for server in BaseTest.SERVERS:
            if server in BaseTest.INSTALLED_SERVER:
                continue
            getattr(j.servers, server).install()

    def setUp(self):
        pass

    @parameterized.expand(BaseTest.SERVERS)
    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/30")
    def Test01_install_option(self, server):
        """
        - ​​​​​Install server . 
        - Make sure that server installed successfully.

        """
        skipped_server = {
            "zdb": "https://github.com/threefoldtech/jumpscaleX_core/issues/30",
            "capacity": "https://github.com/threefoldtech/jumpscaleX_core/issues/94",
            "sanic": {"https://github.com/threefoldtech/jumpscaleX_core/issues/94"},
        }

        if server in skipped_server:
            self.skipTest(skipped_server[server])

        if server in BaseTest.INSTALLED_SERVER:
            self.skipTest("server does't have install option.")
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

        self.info("Install server with default port and get server.")
        getattr(j.servers, server).install()

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
        output, error = self.os_command("netstat -nltp | grep '{}' ".format(server_PID))
        self.assertTrue(output)

        self.info(" * Stop server {}".format(server))
        server.stop()
        output, error = self.os_command("ps -aux | grep -v grep | grep {} | awk '{print $2}'".format(server))
        self.assertFalse(output.decode())

        self.info("* Check that can't connect to server anymore.")
        output, error = self.os_command("netstat -nltp | grep '{}' ".format(server_PID))
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

