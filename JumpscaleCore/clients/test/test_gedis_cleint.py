import random
from Jumpscale import j
from base_test import BaseTest

ACTORS_PATH = (
    "/sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/servers/gedis/pytests/test_package/actors"
)
ACTOR_FILE_1 = "simple"
ACTOR_FILE_2 = "actor"


class TestGedisClient(BaseTest):

    @classmethod
    def setUpClass(cls):
        cls.info("​Get gedis server instance.")
        cls.instance_name = cls.rand_string()
        cls.port = random.randint(1000, 2000)
        cls.gedis_server = j.servers.gedis.get(name=cls.instance_name, port=cls.port, host="0.0.0.0")

        cls.info("Add new actor,Start server ")
        cls.namespace = cls.rand_string()
        cls.gedis_server.actor_add(path="{}/{}.py".format(ACTORS_PATH, ACTOR_FILE_1), namespace=cls.namespace)
        cls.gedis_server.save()
        cls.os_command(
            'tmux new -d -s {} \' kosmos -p "j.servers.gedis.get(name=\\"{}\\").start() "\' '.format(
                cls.rand_string(), cls.instance_name
            )
        )

    @classmethod
    def tearDownClass(cls):
        cls.info("stop gedis server ")
        cls.gedis_server.stop()
        cls.info("make sure that gedis server is stopped correctly")
        output, error = cls.os_command("netstat -nltp | grep '{}' ".format(cls.port))
        cls.assertFalse(output.decode())
        cls.info("delete gedis server")
        cls.gedis_server.delete()

    def setUp(self):
        self.info("create a gedis client")
        self.gedis_client = j.clients.gedis.get(self.rand_string, host="127.0.0.1", port=self.port, namespace=ACTOR_FILE_1)

    def tearDown(self):
        self.info("delete gedis client")
        self.gedis_client.delete()

    def test001_gedis_client_actors_correct_namespace(self):
        """
        TC
        Test case to test gedis client actors, with correct namespace, should success.

        **Test scenario**

        #. check actor method with correct namespace, should succeed.
        #. check that actor loaded and client work successfully.
        """
        actor_ping = self.gedis_client.actors.simple.ping()
        self.assertEqual(actor_ping.decode(), "PONG")

    def test002_gedis_client_actors_wrong_namespace(self):
        """
        TC
        Test case to test gedis client actors, with wrong namespace, should fail.

        **Test scenario**
        #. get actor client with wrong namespace, should fail.
        """
        self.info("Get actor client with wrong namesapce should fail")
        with self.assertRaises(Exception):
            self.gedis_client.actors.NOT_VALID.ping()

    def test004_gedis_ping(self):
        """
        TC
        Test case to test ping method in gedis client, should return true if loaded.

        **Test scenario**
        #. test case to test ping method in gedis client.
        """
        self.info("test case to test ping method in gedis client")
        self.assertTrue(self.gedis_client.ping())
