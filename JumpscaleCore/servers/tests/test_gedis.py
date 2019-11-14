from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest


ACTORS_PATH = (
    "/sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/servers/gedis/pytests/test_package/actors"
)
ACTOR_FILE_1 = "simple"
ACTOR_FILE_2 = "actor"

START_SCRIPT = """ 
server=j.servers.gedis.get(name="{name}")  
server.actor_add(path={actor_path}/{actor_file}.py, namespace="{ns}")  
server.start()  
"""


@unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/128")
class TestGedisServer(BaseTest):
    def setUp(self):
        self.info("​Get gedis server instance.")
        self.instance_name = self.rand_string()
        self.port = random.randint(1000, 2000)
        self.gedis_server = j.servers.gedis.get(name=self.instance_name, port=self.port, host="0.0.0.0")

        self.info("Add new actor,Start server ")
        self.namespace = self.rand_string()
        sc = START_SCRIPT.format(
            name=self.instance_name, actor_path=ACTORS_PATH, actor_file=ACTOR_FILE_1, ns=self.namespace
        )
        cmd = "kosmos -p '{}'".format(sc)
        j.servers.tmux.execute(cmd)

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

    def test02_gedis_client(self):
        """
        - ​Get gedis server instance. 
        - Add  actor ,Start server. 
        - Get actor client with right namespace, should succeed.
        - check that actor loaded and client work successfully.
        - Get actor client with wrong namesapce should raise error.
        - gedis_client ping method, should return True.
        - Test gedis_client reload method with correct namespace, should pass.
        - Test gedis_client reload method with wrong namespcase.
        """
        cl = self.gedis_server.client_get(namespace=self.namespace)
        result = getattr(cl.actors, ACTOR_FILE_1).ping()
        self.assertEqual(result.decode(), "PONG")

        self.info("Get actor client with wrong namesapce should raise error")
        with self.assertRaises(Exception):
            wrong_namespace = self.rand_string()
            cl = self.gedis_server.client_get(namespace=wrong_namespace)

        self.info("gedis_client ping method, should return True")
        self.assertTrue(cl.ping())

        self.info("Test gedis_client reload method with correct namespace, should pass")
        cl.reload(namespace=ACTOR_FILE_1)
        result = getattr(cl.actors, ACTOR_FILE_1).ping()
        self.assertEqual(result.decode(), "PONG")

        self.info("Test gedis_client reload method with wrong namespcase")
        with self.assertRaises(Exception):
            cl.reload(namespace="WRONG_NAMESPACE")

    def test03_gedis_add_actors(self):
        """
        - ​Get gedis server instance. 
        - Use add_actors method.
        - check that actors added and client can get from both of them .
        """
        self.gedis_server.stop()
        sc = """ 
            server=j.servers.gedis.get(name={name})  
            server.actors_add(path={actor_path},namespace={ns}) 
            server.start()  
            """.format(
            name=self.instance_name, actor_path=ACTORS_PATH, ns=self.namesapce
        )
        cmd = "kosmos -p '{}'".format(sc)
        j.servers.tmux.execute(cmd)

        self.assertIn(ACTOR_FILE_2, self.gedis_server.actors_list(self.namespace))
        cl = self.gedis_server.client_get(namespace=self.namespace)
        arg_1 = random.randint(11, 55)
        arg_2 = random.randint(66, 99)
        result = getattr(cl.actors, ACTOR_FILE_2).args_in(arg_1, arg_2)
        self.assertEqual("{} {} ".format(arg_1, arg_2), result.decode())

    def test04_gedis_load_actors(self):
        """
        - ​Add actor to actors_data
        - Use load_actors.
        - check that actor loaded successfully.
        """
        self.gedis_server.stop()

        sc = """ 
            server=j.servers.gedis.get(name={name})  
            server.actors_data = "{ns}:{actor_path}/{actor_file}.py".format(self.namespace, ACTORS_PATH, ACTOR_FILE_2)
            server.load_actors()
            server.start()  
            """.format(
            name=self.instance_name, actor_path=ACTORS_PATH, ns=self.namespace, actor_file=ACTOR_FILE_2
        )
        cmd = "kosmos -p '{}'".format(sc)
        j.servers.tmux.execute(cmd)

        self.assertIn(ACTOR_FILE_2, self.gedis_server.actors_list(self.namespace))
        cl = self.gedis_server.client_get(namespace=self.namespace)
        arg_1 = random.randint(11, 55)
        arg_2 = random.randint(66, 99)
        result = getattr(cl.actors, ACTOR_FILE_2).args_in(arg_1, arg_2)
        self.assertEqual("{} {} ".format(arg_1, arg_2), result.decode())
