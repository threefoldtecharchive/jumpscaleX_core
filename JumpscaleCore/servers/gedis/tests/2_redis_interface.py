from Jumpscale import j
from io import BytesIO
import binascii


def main(self):
    """
    kosmos -p 'j.servers.gedis.test("redis_interface")'
    """

    # lets make sure we have the right package loaded
    package_path = "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/examples/ibiza"
    cl = self._threebot_client_default
    # if reload==False then the package will not be reloaded if its already there
    cl.actors.package_manager.package_add("ibiza_test", path=package_path, reload=False)
    cl.reload()

    # next only works because the test is running in the threebot itself, so I can use the installed package code
    ibiza_client = j.threebot.package.ibiza.client_get()

    r0 = ibiza_client.actors.ibiza_actor.info("aaa")
    assert r0 == b"aaa"

    ### HOW TO REDIS

    cl = j.clients.redis.get(port=8901)  # towards gevent

    assert cl.ping()

    # execute a command without arguments on no actor namespace
    assert cl.execute_command("PING")

    # OLD STYLE REDIS COMMAND USAGE

    data = {}
    data = {"a": 1}
    data2 = j.data.serializers.json.dumps(data)

    # $namespace.$actorname.$methodname
    # data needs to be positional if not schema_in used like in this example
    data3 = cl.execute_command("ibiza.ibiza_actor.info", data2)

    assert data2 == data3.decode()

    ############

    # NEW STYLE REDIS COMMAND USAGE (FORCE JSON OR MSGPACK INPUT, MORE RELIABLE !!!)
    # WILL ONLY PLAY A ROLE WHEN A SCHEMA_IN is used to strongly type the method arguments

    cl.execute_command("config_format", "json")  # json or msgpack
    ##you can have separate in/out formats
    # cl.execute_command("config_format_in", "json")  # json or msgpack
    # cl.execute_command("config_format_out", "json")  # json or msgpack

    data = {"a": "a", "b": False, "c": 3}
    data2 = j.data.serializers.json.dumps(data)

    data3 = cl.execute_command("ibiza.painter.example3", data2)
    assert data3 == b'{"a": "a", "b": true, "c": 3}'
