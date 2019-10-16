from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest


class TestZdbServer(BaseTest):
    def setUp(self):
        self.info("​Install zdb server.")
        j.servers.zdb.install()

        self.info("Start zdb server")
        self.zdb = j.servers.zdb.get()
        self.zdb.start()

    def test01_client_admin_get_and_client_get_and_destroy(self):
        """
        - ​Install zdb server.
        - Start zdb server .
        - Create namespace using client_admin_get.
        - Get zdb client and make sure it works correctly .
        - Destroy zdb server.
        - Check that server stopped and database removed successfully.
        """
        self.info("Create namespace using client_admin_get.")
        admin_client = self.zdb.client_admin_get()
        namespace = self.rand_string()
        result = admin_client.namespace_new(namespace)
        self.assertEqual(result.nsname, namespace)

        self.info("Get zdb client and make sure it works correctly ")
        zdb_client = self.zdb.client_get(namespace=namespace)
        data = self.rand_string()
        id = zdb_client.set(data)
        self.assertEqual(id, 0)
        self.assertEqual(data, zdb_client.get(id).decode())

        self.info(" Destroy zdb server")
        zdb_client.destroy()

        self.info("Check that server stopped and database removed successfully.")
        output, error = self.os_command(" ps -aux | grep -v grep | grep zdb ")
        self.assertFalse(output.decode())

        output, error = self.os_command(" ls /sandbox/var/zdb")
        self.assertNotIn(self.zdb.name, output.decode())
