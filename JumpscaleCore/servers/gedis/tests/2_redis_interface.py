from Jumpscale import j


def main(self):
    """
    kosmos -p 'j.servers.gedis.test("redis_interface")'
    """

    cl = j.clients.redis.get(port=8920)

    assert cl.ping()

    # execute a command without arguments on no actor namespace
    assert cl.execute_command("PING")

    j.shell()

    print("**DONE**")
