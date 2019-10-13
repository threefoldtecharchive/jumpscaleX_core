from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest


class TestThreebotServer(BaseTest):
    def setUp(self):
        j.servers.threebot.install()
        self.threebot_server = j.servers.threebot.get()
        self.threebot_server.start(background=True)

    def Teardown(self):
        self.threebot_server.stop()

    def test01_local_start_default(self):
        """
        - ​Install  threebot server.
        - Get gedis client from it.
        - Check it works correctly.
        """
        self.info("Get gedis client from it .")
        gedis_client = j.servers.threebot.local_start_default()

        self.info("Check it works correctly.")
        self.assertTrue(gedis_client.ping())

    def test02_get_bcdb(self):
        """
        - ​Install  threebot server.
        - Use bcdb_get to create new bcdb, check it created successfully.
        """
        self.info("Use get_bcdb to create new bcdb, check it created successfully.")
        bcdb_name = self.rand_string()
        self.threebot_server.bcdb_get(name=bcdb_name)
        output, error = self.os_command(" ls /sandbox/var/bcdb")
        self.assertNotIn(bcdb_name, output.decode())

    def Test03_start_stop_options(self, server):
        """
        - Start server. 
        - Make sure that server started successfully by check zdb and sonic works.   
        - Check that server connection  works successfully.
        - Stop server
        - Check that can't connect to server anymore.
        """
        self.info(" *  Make sure that server started successfully by check zdb and sonic works.  ")
        output, error = self.os_command(" ps -aux | grep -v grep | grep startupcmd_zdb  | awk '{{print $2}}'")
        self.assertTrue(output.decode())
        zdb_PID = int(output.decode())

        output, error = self.os_command(" ps -aux | grep -v grep | grep startupcmd_sonic  | awk '{{print $2}}'")
        self.assertTrue(output.decode())
        sonic_PID = int(output.decode())

        self.info(" * Check that server connection  works successfully.")
        output, error = self.os_command("netstat -nltp | grep '{}' ".format(sonic_PID))
        self.assertTrue(output)

        output, error = self.os_command("netstat -nltp | grep '{}' ".format(zdb_PID))
        self.assertTrue(output)

        self.info(" * Stop server {}".format(server))
        self.threebot_server.stop()
        output, error = self.os_command("ps -aux | grep -v grep | grep -e startupcmd_sonic -e startupcmd_zdb")
        self.assertFalse(output.decode())

        self.info("* Check that can't connect to server anymore.")
        output, error = self.os_command("netstat -nltp | grep -e {}  -e {}".format(sonic_PID, zdb_PID))
        self.assertFalse(output)
