from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest


ACTORS_PATH = (
    "/sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/servers/gedis/pytests/test_package/actors"
)
ACTOR_FILE_1 = "simple"
ACTOR_FILE_2 = "actor"

#
@unittest.SkipTest
class TestGedisServer(BaseTest):
    def setUp(self):
        self.info("​Get gedis server instance.")
        self.instance_name = self.rand_string()
        self.port = random.randint(1000, 2000)
        self.gedis_server = j.servers.gedis.get(name=self.instance_name, port=self.port, host="0.0.0.0")

        self.info("Add new actor,Start server ")
        self.namespace = self.rand_string()
        self.gedis_server.actor_add(path="{}/{}.py".format(ACTORS_PATH, ACTOR_FILE_1), namespace=self.namespace)
        self.gedis_server.save()
        self.os_command(
            'tmux new -d -s {} \' kosmos -p "j.servers.gedis.get(name=\\"{}\\").start() "\' '.format(
                self.rand_string(), self.instance_name
            )
        )

    def tearDown(self):
        self.gedis_server.stop()
        output, error = self.os_command("netstat -nltp | grep '{}' ".format(self.port))
        self.gedis_server.delete()
        self.assertFalse(output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test01_actor_add(self):
        """
        - ​Get gedis server instance. 
        - Add new actor,Start server. 
        - Check that actor added successfully.
        """
        self.info("Check that actor added successfully.")
        self.assertIn(self.namespace, self.gedis_server.actors_list(self.namespace))

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/92")
    def test02_actors_methods_list(self):
        """
        - ​Get gedis server instance. 
        - Add two actors ,Start server. 
        - Check that actors methods list works correctly.
        """
        self.info("Add two actors ,Start server.")
        self.gedis_server.stop()
        self.gedis_server.actor_add(path="{}/{}.py".format(ACTORS_PATH, ACTOR_FILE_2), namespace=self.namespace)
        self.os_command(
            'tmux new -d -s {} \' kosmos -p "j.servers.gedis.get(name=\\"{}\\").start() "\' '.format(
                self.rand_string(), self.instance_name
            )
        )

        self.info(" Check that actors methods list works correctly.")
        methods_list = self.gedis_server.actors_methods_list(name=self.namespace)
        self.assertIn("foo", methods_list)
        self.assertIn("schema_out", methods_list)

    def test03_gedis_client(self):
        """
        - ​Get gedis server instance. 
        - Add  actor ,Start server. 
        - Get actor client with right namespace, should succeed.
        - check that actor loaded and client work successfully.
        - Get actor client with wrong namesapce should raise error. 
        """
        cl = self.gedis_server.client_get(namespace=self.namespace)
        result = getattr(cl.actors, ACTOR_FILE_1).ping()
        self.assertEqual(result.decode(), "PONG")

        self.info("Get actor client with wrong namesapce should raise error")
        with self.assertRaises(Exception):
            wrong_namespace = self.rand_string()
            cl = self.gedis_server.client_get(namespace=wrong_namespace)

    def test04_gedis_add_actors(self):
        """
        - ​Get gedis server instance. 
        - Use add_actors method.
        - check that actors added and client can get from both of them .
        """
        self.gedis_server.stop()
        self.gedis_server.actors_add(path=ACTORS_PATH, namespace=self.namespace)
        self.os_command(
            'tmux new -d -s {} \' kosmos -p "j.servers.gedis.get(name=\\"{}\\").start() "\' '.format(
                self.rand_string(), self.instance_name
            )
        )

        self.assertIn(ACTOR_FILE_2, self.gedis_server.actors_list(self.namespace))
        cl = self.gedis_server.client_get(namespace=self.namespace)
        arg_1 = random.randint(11, 55)
        arg_2 = random.randint(66, 99)
        result = getattr(cl.actors, ACTOR_FILE_2).args_in(arg_1, arg_2)
        self.assertEqual("{} {} ".format(arg_1, arg_2), result.decode())

    def test05_gedis_load_actors(self):
        """
        - ​Add actor to actors_data
        - Use load_actors.
        - check that actor loaded successfully.
        """
        self.gedis_server.stop()

        self.gedis_server.actors_data = "{}:{}/{}.py".format(self.namespace, ACTORS_PATH, ACTOR_FILE_2)
        self.gedis_server.load_actors()

        self.os_command(
            'tmux new -d -s {} \' kosmos -p "j.servers.gedis.get(name=\\"{}\\").start() "\' '.format(
                self.rand_string(), self.instance_name
            )
        )
        self.assertIn(ACTOR_FILE_2, self.gedis_server.actors_list(self.namespace))
        cl = self.gedis_server.client_get(namespace=self.namespace)
        arg_1 = random.randint(11, 55)
        arg_2 = random.randint(66, 99)
        result = getattr(cl.actors, ACTOR_FILE_2).args_in(arg_1, arg_2)
        self.assertEqual("{} {} ".format(arg_1, arg_2), result.decode())
