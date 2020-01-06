from unittest import TestCase, skip
from subprocess import run, PIPE
from uuid import uuid4
from time import sleep

from Jumpscale import j
from parameterized import parameterized
from loguru import logger
from redis import ResponseError, AuthenticationError

from base_test import BaseTest


class TestRedisConfig(BaseTest):

    startup = None
    redis_client = None

    def tearDown(self):
        if self.startup:
            self.startup.stop()
            self.startup.delete()
        if self.redis_client:
            self.redis_client.delete()

        j.clients.redis._cache_clear()
        j.sal.process.killProcessByName("redis-server")
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        j.clients.redis.core_get(reset=True)

    def start_redis_server(self, port=None, password=False):
        if port:
            cmd = f"redis-server --port {port}"

        else:
            passwd = ""
            if password:
                passwd = "sed -i 's/# requirepass foobared/requirepass test/g' /tmp/redis.conf"
            cmd = f"""
            cp /etc/redis/redis.conf /tmp
            sed -i 's/port 6379/port 0/g' /tmp/redis.conf
            {passwd}
            echo "unixsocket /tmp/redis.sock" >> /tmp/redis.conf
            echo "unixsocketperm 775" >> /tmp/redis.conf
            redis-server /tmp/redis.conf
            """
        self.startup = j.servers.startupcmd.get("test_redis_config", cmd_start=cmd)
        self.startup.start()

    def wait_for_server(self, port=None):
        if port:
            response = j.sal.nettools.waitConnectionTest(ipaddr="localhost", port=port, timeout=5)
            return response
        else:
            for _ in range(5):
                output, error = self.os_command("fuser -a /tmp/redis.sock")
                if output:
                    sleep(1)
                    return True
                sleep(1)

    @parameterized.expand(["port", "unixsocket"])
    def test001_get_redisclient_using_port_unixsocket(self, type):
        """TC564
        Test case for getting redis client using port/unixsocket.
        
        **Test scenario**
        #. Start redis server on port/unixsocket.
        #. Get redis client using port/unixsocket.
        #. Try to ping the server, should succeed.
        """
        self.info(f"Start redis server on {type}.")
        if type == "port":
            port = self.rand_num(10000, 11000)
            self.start_redis_server(port=port)
            self.wait_for_server(port=port)
        else:
            self.start_redis_server()
            self.wait_for_server()

        self.info(f"Get redis client using {type}.")
        name = self.rand_string()
        if type == "port":
            self.redis_client = j.clients.redis_config.get(name=name, port=port)
        else:
            self.redis_client = j.clients.redis_config.get(name=name, unixsocket="/tmp/redis.sock", port=0, addr=None)
        cl = self.redis_client.redis

        self.info("Try to ping the server, should succeed.")
        self.assertTrue(cl.ping())

    @parameterized.expand([(False,), (True,)])
    def test002_set_password(self, password):
        """TC565
        Test case for getting redis client with/without password.
        
        **Test scenario**
        #. Start redis server on unixsocket with password.
        #. Try to get redis client with/without password, should succeed/fail.
        """
        self.info("Start redis server on unixsocket with password.")
        self.start_redis_server(password=True)
        self.wait_for_server()

        self.info(f"Try to get redis client with password={password}")
        name = self.rand_string()
        if password:
            self.redis_client = j.clients.redis_config.get(
                name=name, unixsocket="/tmp/redis.sock", port=0, addr=None, password_="test"
            )
            cl = self.redis_client.redis
            self.assertTrue(cl.ping())
        else:
            self.redis_client = j.clients.redis_config.get(name=name, unixsocket="/tmp/redis.sock", port=0, addr=None)
            with self.assertRaises((ResponseError, AuthenticationError)) as e:
                cl = self.redis_client.redis
            self.assertIn("Authentication required", e.exception.args[0])

    @parameterized.expand([(True,), (False,)])
    def test003_set_patch(self, patch):
        """TC566
        Test case for getting redis client with/without setting patch.
        
        **Test scenario**
        #. Start redis server on a random port.
        #. Get redis client with/without setting patch.
        #. Try to set data on redis, should return "OK" in case of patching and "True" in case of no patching.
        #. Get the value of the key has been set, should succeed.
        #. Delete this key, should return 1 (in different servers may return the key in case of patching)
        #. Try to get the value of this key, should return 0.
        """
        self.info("Start redis server on a random port.")
        port = self.rand_num(10000, 11000)
        self.start_redis_server(port=port)
        self.wait_for_server(port=port)

        self.info(f"Get redis client with set_patch={patch}.")
        name = self.rand_string()
        self.redis_client = j.clients.redis_config.get(name=name, port=port, set_patch=patch)
        cl = self.redis_client.redis
        self.assertTrue(cl.ping())

        self.info("Try to set data on redis")
        key = self.rand_string()
        value = self.rand_string()
        response = cl.set(name=key, value=value)
        if patch:
            self.assertEqual(response, b"OK")
        else:
            self.assertEqual(response, True)
        self.info("Get the value of the key has been set, should succeed.")
        result = cl.get(name=key)
        self.assertEqual(result.decode(), value)

        self.info("Delete this key, should return 1")
        # should return different value in case of another server is used.
        response = cl.delete(key)
        self.assertEqual(response, 1)

        self.info("Try to get the value of this key, should return 0")
        result = cl.get(name=key)
        self.assertFalse(result)
