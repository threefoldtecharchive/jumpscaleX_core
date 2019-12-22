from Jumpscale import j
from base_test import BaseTest
from parameterized import parameterized
import random, requests, uuid, unittest
from requests import ConnectionError

SKIPPED_INSTALLATION = {
    "capacity": "https://github.com/threefoldtech/jumpscaleX_core/issues/94",
    "sanic": "https://github.com/threefoldtech/jumpscaleX_core/issues/94",
    "flask": "https://github.com/threefoldtech/jumpscaleX_core/issues/94",
    "sockexec": "https://github.com/threefoldtech/jumpscaleX_core/issues/30",
    "errbot": "https://github.com/threefoldtech/jumpscaleX_core/issues/94",
    "etcd": "https://github.com/threefoldtech/jumpscaleX_core/issues/158",
    "odoo": "https://github.com/threefoldtech/jumpscaleX_core/issues/222",
}


class TestServers(BaseTest):
    @classmethod
    def setUpClass(cls):

        for server in BaseTest.SERVERS:
            if server in BaseTest.INSTALLED_SERVER or server in SKIPPED_INSTALLATION:
                continue
            getattr(j.servers, server).install()

    def setUp(self):
        pass

    @parameterized.expand(BaseTest.SERVERS)
    def Test01_install_option(self, server):
        """
        - ​​​​​Install server . 
        - Make sure that server has been installed successfully.

        """
        if server in SKIPPED_INSTALLATION:
            self.skipTest(SKIPPED_INSTALLATION[server])

        if server in BaseTest.INSTALLED_SERVER:
            self.skipTest("server does't have install option.")

        self.info("Make sure that server has been installed successfully.")
        if server == "threebot":
            output, error = self.os_command("openresty --help")
            self.assertIn("Usage", output.decode())

        else:
            output, error = self.os_command("{} --help".format(server))
            if server == "zdb":
                self.assertIn("Command line arguments:", output.decode())
            elif server in ["sonic", "corex"]:
                self.assertIn("USAGE:", output.decode())
            elif server in ["odoo"]:
                self.assertIn("Usage:", output.decode())
            else:
                self.assertIn("usage", output.decode())

    @parameterized.expand(BaseTest.SERVERS)
    def Test02_start_stop_options(self, server):
        """
        - Start server. 
        - Make sure that server started successfully.   
        - Check that server connection  works successfully.
        - Stop server
        - Check that can't connect to server anymore.
        """
        skipped = {"gedis_websocket": "https://github.com/threefoldtech/jumpscaleX_core/issues/30"}
        if server in SKIPPED_INSTALLATION:
            self.skipTest(SKIPPED_INSTALLATION[server])
        elif server in skipped:
            self.skipTest(skipped[server])

        self.info("* Start Server {}".format(server))
        if server in ["etcd"]:
            server_object = getattr(j.servers, server)
            server_process = j.core.tools.text_replace("{DIR_BASE}/bin/etcd")

        else:
            server_object = getattr(j.servers, server).get()
            server_process = "startupcmd_{}".format(server)

        server_object.start()

        self.info(" * Make sure that server started successfully.")
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux | grep {} | awk '{{print $2}}'".format(server_process)
        )
        self.assertTrue(output.decode())
        server_PID = int(output.decode())

        self.info(" * Check that server connection  works successfully.")
        if server == "odoo":
            server_element = server_object.port
        else:
            server_element = server_PID

        output, error = self.os_command("netstat -nltp | grep '{}' ".format(server_element))
        self.assertTrue(output)

        self.info(" * Stop server {}".format(server))
        server_object.stop()
        output, error = self.os_command("ps -aux | grep -v grep | grep {}".format(server_process))
        self.assertFalse(output.decode())

        self.info("* Check that can't connect to server anymore.")
        output, error = self.os_command("netstat -nltp | grep {}".format(server_element))
        self.assertFalse(output)
