import os
import time
from multiprocessing import Process

import gevent
import pytest
from Jumpscale import j
import redis

from .actors.actor import SCHEMA_IN, SCHEMA_OUT


class TestSimpleEcho:
    def setup(self):
        self.server = j.servers.gedis.configure(name="test", port=8889, host="0.0.0.0", ssl=False, password="")
        actor_path = os.path.join(os.path.dirname(__file__), "actors/actor.py")
        self.server.actor_add(actor_path)
        self.proc = Process(target=self.server.start, args=())
        self.proc.start()
        # self.gl = gevent.spawn(self.server.start)
        wait_start_server("127.0.0.1", 8889)

    def teardown(self):
        # self.gl.kill()
        # self.gl.join()
        self.proc.terminate()
        self.proc.join()

    def test_ping(self):
        client = self.server.client_get()
        assert b"pong" == client.actors.actor.ping()
        assert b"test" == client.actors.actor.echo("test")
        time.sleep(2)

    def test_schema_in(self):
        client = self.server.client_get()
        x = j.data.schema.get_from_url(url="gedis.test.in").new()
        x.foo = "test"
        assert b"test" == client.actors.actor.schema_in(x)

    def test_schema_out(self):
        time.sleep(2)
        client = self.server.client_get()
        result = client.actors.actor.schema_out()
        assert result.bar == "test"

    def test_schema_in_out(self):
        client = self.server.client_get()
        x = j.data.schema.get_from_url(url="gedis.test.in").new()
        x.foo = "test"
        result = client.actors.actor.schema_in_out(x)
        assert result.bar == x.foo

    def test_schema_in_list_out(self):
        client = self.server.client_get()
        x = j.data.schema.get_from_url(url="gedis.test.in").new()
        x.foo = "test"
        result = client.actors.actor.schema_in_list_out(x)
        assert isinstance(result, list)
        # assert result.bar == x.foo

    def test_args_in(self):
        client = self.server.client_get()

        with pytest.raises((ValueError, TypeError)):
            client.actors.actor.args_in(12, "hello")

        with pytest.raises((ValueError, TypeError)):
            client.actors.actor.args_in({"foo"}, "hello")

        assert b"hello 1" == client.actors.actor.args_in("hello", 1)

    def test_error(self):
        client = self.server.client_get()

        with pytest.raises(redis.exceptions.ResponseError):
            client.actors.actor.raise_error()

        # ensure the connection is still valid after an exception
        assert client.ping()


def wait_start_server(addr, port):
    j.tools.timer.execute_until(
        lambda: j.sal.nettools.tcpPortConnectionTest(addr, port, timeout=1), timeout=5, interval=0.2
    )
