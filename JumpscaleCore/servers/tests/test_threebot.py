from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest
from parameterized import parameterized

MAIN_ACTORS = ["package_manager", "sonic", "gdrive", "myjobs", "identity", "chatbot"]


class TestThreebotServer(BaseTest):
    def setUp(self):
        self.info("install threebot server.")
        j.servers.threebot.install()
        self.threebot_server = j.servers.threebot.get()

    def Teardown(self):
        self.threebot_server.stop()

    def check_threebot_main_running_servers(self, web=True):
        self.info(" *  Make sure that server started successfully by check zdb ,lapis, sonic,and openresty work.  ")

        self.info("*** zdb server ***")
        zdb_output, error = self.os_command(" ps -aux | grep -v grep | grep startupcmd_zdb  | awk '{{print $2}}'")
        self.assertTrue(zdb_output, "can't find zdb server.")
        zdb_PID = int(zdb_output.decode())
        self.info(" * Check that  zdb server connection  works successfully.")
        output, error = self.os_command("netstat -nltp | grep '{}' ".format(zdb_PID))
        self.assertTrue(output, "zdb server connection doesn't work.")

        self.info("*** sonic  server ***")
        sonic_output, error = self.os_command(" ps -aux | grep -v grep | grep startupcmd_sonic  | awk '{{print $2}}'")
        self.assertTrue(sonic_output.decode(), "can't find sonic server ")
        sonic_PID = int(sonic_output.decode())
        self.info(" * Check that  sonic server connection  works successfully.")
        output, error = self.os_command("netstat -nltp | grep '{}' ".format(sonic_PID))
        self.assertTrue(output, "sonic server connection doesn't work.")

        self.info("*** lapis server ***")
        lapis_output, error = self.os_command(" ps -aux | grep -v grep | grep lapis ")
        self.assertTrue(lapis_output.decode(), "can't find lapis server ")

        if web:
            self.info("*** openresty ***")
            lapis_output, error = self.os_command(" ps -aux | grep -v grep | grep /sandbox/bin/openresty ")
            self.assertTrue(lapis_output.decode(), "can't find openresty server ")

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

        self.info(" Check that main servers running successfully.  ")
        self.check_threebot_main_running_servers()

        self.info("check main actors loaded successfully.")
        for actor in MAIN_ACTORS:
            try:
                getattr(gedis_client.actors, actor)
            except Exception as e:
                self.fail(e)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/208")
    def test02_get_bcdb(self):
        """
        - ​Install  threebot server.
        - Use bcdb_get to create new bcdb, check it created successfully.
        """
        self.info("Use get_bcdb to create new bcdb, check it created successfully.")
        self.threebot_server.start(background=True)
        bcdb_name = self.rand_string()
        self.threebot_server.bcdb_get(name=bcdb_name)
        output, error = self.os_command(" ls /sandbox/var/bcdb")
        self.assertNotIn(bcdb_name, output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/208")
    def Test03_start_stop_options(self, server):
        """
        - Start server. 
        - Make sure that server started successfully by check zdb and sonic works.   
        - Check that server connection  works successfully.
        - Stop server
        """
        self.threebot_server.start(background=True)
        self.info(" Check that main servers running successfully.  ")
        self.check_threebot_main_running_servers()

        self.info(" * Stop server {}".format(server))
        self.threebot_server.stop()
        output, error = self.os_command("ps -aux | grep -v grep | grep -e startupcmd_sonic -e startupcmd_zdb")
        self.assertFalse(output.decode())

    @parameterized.expand([(True,), (False,)])
    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/208")
    def test04_verify_start_options(self, web_status):
        """
        - ​Install  threebot server.
        - Start threebot server with web = False, check that right servers started successfully.
        - Start threebot server with web = True, Check that right server started successfully
        """
        self.info("Start threebot server with web = False, check that right servers started successfully.")
        self.threebot_server.start(web=web_status)

        self.info(" Check that main servers running successfully.  ")
        self.check_threebot_main_running_servers()

        if web_status:
            self.info(" Check that main servers running successfully include openresty server.  ")
            self.check_threebot_main_running_servers(web=web_status)
