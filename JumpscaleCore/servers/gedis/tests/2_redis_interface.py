from Jumpscale import j


def main(self):
    """
    kosmos -p 'j.servers.gedis.test("redis_interface")'
    """
    r0 = self.client.actors.ibiza_actor.info("aaa")

    cl = j.clients.redis.get(port=8901)

    assert cl.ping()

    # execute a command without arguments on no actor namespace
    assert cl.execute_command("PING")

    # OLD STYLE REDIS COMMAND USAGE

    data = {}
    data = {"a": 1}
    data2 = j.data.serializers.json.dumps(data)

    # $namespace.$actorname.$methodname
    # data needs to be positional if not schema_in used like in this example
    # data3 = cl.execute_command("ibiza.ibiza_actor.info", data2)

    # TODO: why is the namespace default !!!! ERROR
    data3 = cl.execute_command("default.ibiza_actor.info", data2)

    assert data2 == data3.decode()

    # NEW STYLE REDIS COMMAND USAGE

    j.shell()

    print("**DONE**")
