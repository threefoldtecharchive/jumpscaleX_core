import logging
from time import sleep
from unittest import TestCase

from Jumpscale import j
from parameterized import parameterized
from redis import AuthenticationError, ResponseError

startup = None
redis_client = None
redis_port = None


def after():
    global redis_port
    if startup:
        startup.stop()
        startup.delete()
    if redis_client:
        redis_client.delete()

    j.clients.redis._cache_clear()
    if redis_port:
        j.sal.process.killProcessByPort(redis_port)
        redis_port = None
    else:
        j.sal.process.killProcessByName("redis-server 127.0.0.1")


def info(message):
    j.tools.logger._log_info(message)


def rand_num(start=100, stop=1000):
    return j.data.idgenerator.generateRandomInt(start, stop)


def rand_string():
    return j.data.idgenerator.generateXCharID(10)


def start_redis_server(port=None, password=False):
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
    startup = j.servers.startupcmd.get("test_redis_config", cmd_start=cmd)
    startup.start()


def wait_for_server(port=None):
    if port:
        response = j.sal.nettools.waitConnectionTest(ipaddr="localhost", port=port, timeout=5)
        return response
    else:
        for _ in range(5):
            _, output, error = j.sal.process.execute("fuser -a /tmp/redis.sock", die=False)
            if output:
                sleep(1)
                return True
            sleep(1)


@parameterized.expand(["port", "unixsocket"])
def test001_get_redisclient_using_port_unixsocket(type):
    """TC564
    Test case for getting redis client using port/unixsocket.

    **Test scenario**
    #. Start redis server on port/unixsocket.
    #. Get redis client using port/unixsocket.
    #. Try to ping the server, should succeed.
    """
    info(f"Start redis server on {type}.")
    global redis_port
    if type == "port":
        port = rand_num(10000, 11000)
        start_redis_server(port=port)
        wait_for_server(port=port)
        redis_port = port
    else:
        start_redis_server()
        wait_for_server()

    info(f"Get redis client using {type}.")
    name = rand_string()
    if type == "port":
        redis_client = j.clients.redis_config.get(name=name, port=port)
    else:
        redis_client = j.clients.redis_config.get(name=name, unixsocket="/tmp/redis.sock", port=0, addr=None)
    cl = redis_client.redis

    info("Try to ping the server, should succeed.")
    assert cl.ping()


@parameterized.expand([(False,), (True,)])
def test002_set_password(password):
    """TC565
    Test case for getting redis client with/without password.

    **Test scenario**
    #. Start redis server on unixsocket with password.
    #. Try to get redis client with/without password, should succeed/fail.
    """
    info("Start redis server on unixsocket with password.")
    start_redis_server(password=True)
    wait_for_server()

    info(f"Try to get redis client with password={password}")
    name = rand_string()
    if password:
        redis_client = j.clients.redis_config.get(
            name=name, unixsocket="/tmp/redis.sock", port=0, addr=None, secret_="test"
        )
        cl = redis_client.redis
        assert cl.ping()
    else:
        redis_client = j.clients.redis_config.get(name=name, unixsocket="/tmp/redis.sock", port=0, addr=None)
        t = TestCase()
        with t.assertRaises((ResponseError, AuthenticationError)) as e:
            cl = redis_client.redis
        assert "Authentication required" in e.exception.args[0]


@parameterized.expand([(True,), (False,)])
def test003_set_patch(patch):
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
    info("Start redis server on a random port.")
    global redis_port
    port = rand_num(10000, 11000)
    start_redis_server(port=port)
    wait_for_server(port=port)
    redis_port = port

    info(f"Get redis client with set_patch={patch}.")
    name = rand_string()
    redis_client = j.clients.redis_config.get(name=name, port=port, set_patch=patch)
    cl = redis_client.redis
    assert cl.ping()

    info("Try to set data on redis")
    key = rand_string()
    value = rand_string()
    response = cl.set(name=key, value=value)
    if patch:
        assert response == b"OK"
    else:
        assert response == True
    info("Get the value of the key has been set, should succeed.")
    result = cl.get(name=key)
    assert result.decode() == value

    info("Delete this key, should return 1")
    # should return different value in case of another server is used.
    response = cl.delete(key)
    assert response == 1

    info("Try to get the value of this key, should return 0")
    result = cl.get(name=key)
    assert result is None
