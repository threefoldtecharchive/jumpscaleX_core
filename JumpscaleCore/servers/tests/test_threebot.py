from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest


class TestThreebotServer(BaseTest):
    def setUp(self):
        j.servers.threebot.install()
        self.threebot_server = j.servers.threebot.get()
        self.threebot_server.start(background=True)

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

