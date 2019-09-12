from Jumpscale impor j 
from base_test import BaseTest
from parameterized import parameterized
import random ,uuid , requests
from requests import ConnectionError

class TestServers(BaseTest):

    def setUp(self):
        pass
    
    @parameterized.expand(self.servers.keys())
    def Test01_install_option(selef, server):
        """
        - ​​​​​Install server . 
        - Make sure that server installed successfully.

        """
        if "install" not in self.servers[server].keys():
            pass 
        self.log("Install Server %s".format(server))
        getattr(j.servers, server).install()

        self.log("Make sure that server installed successfully.")
        output, error = self.os_command("%s --help".format(server))
        self.assertIn(self.servers[server]["install"], output.decode())
    
    
    @parameterized.expand(self.servers.keys())
    def Test02_start_stop_options(selef, server):
        """
        - Start server . 
        - Make sure that server started successfully.
        - Check that server connection  works successfully.
        - Stop server
        - Check that can't connect to server anymore.
        """
        if "start" not in self.servers[server].keys():
            pass 
        self.log("Start Server %s".format(server))
        server = getattr(j.servers, server).get()
        server.start()
        self.log("Make sure that server started successfully.")
        output, error = self.os_command("ps -aux | grep {}".format(server))
        self.assertTrue(output.decode())

        self.log("Check that server connection  works successfully.")
        response = requests.get("http://127.0.0.1:{}".format(server.port))
        self.assertEqual(response.status_code, 200)

        self.log("Stop server {}".format(server))
        server.stop()
        output, error = self.os_command("ps -aux | grep {}".format(server))
        self.assertFalse(output.decode())

        self.log("Check that can't connect to server anymore.")
        try:
            response = requests.get("http://127.0.0.1:{}".format(server.port))
            self.assertNotEqual(response.status_code,200)
        except ConnectionError as e :
            seslf.assertIn("Failed to establish a new connection", e)

    @parameterized.expand(self.servers.keys())
    def Test03_port_and_name_options(selef, server):
        """
        - install server with default port and get server.
        - Make sure that server started successfully.

        """
        self.log("Install server with default port and get server.")
        getattr(j.servers, server).install()
        server = getattr(j.servers, server).get()

        self.log("Change server port and name. ")
        new_port = random.randint(2000,3000)
        new_name = str(uuid.uuid4()).replace('-', '')[1:10]
        server.port = new_ports
        server.name = new_name

        self.log("​​​​​Start the server and check the  port server started with")
        server.start()
        output, error = self.os_command("ps -aux | grep {}".format(server))
        self.assertIn(new_port, output.decode())
        self.assertIn(new_name,output.decode())

   