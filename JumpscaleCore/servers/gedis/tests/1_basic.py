from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.gedis.test("basic")'
    """

    print("[*] testing echo")
    client = j.clients.gedis.get("gedis_test", port=8888, namespace="ibiza")

    actors_path = "/sandbox/code/github/threefoldtech/digitalmeX/packages/extra/examples/actors"
    client.actors.system.actors_add_path(namespace="ibiza", path=actors_path)

    client.actors
    assert client.ping()

    assert client.actors.painter.echo("s") == b"s"
    print("- done")

    print("[*] testing set with schemas")
    print("[1] schema_in as schema url")
    wallet_out1 = client.actors.painter.example1(addr="testaddr")
    assert wallet_out1.addr == "testaddr"
    print("[1] Done")

    print("[2] schema_in as inline schema with url")
    wallet_schema = j.data.schema.get_from_url(url="jumpscale.example.wallet")
    wallet_in = wallet_schema.new()
    wallet_in.addr = "testaddr"
    wallet_in.jwt = "testjwt"

    wallet_out = client.actors.painter.example2(wallet_in)

    assert wallet_in.addr == wallet_out.addr
    assert wallet_in.jwt == wallet_out.jwt
    print("[2] Done")

    print("[3] inline schema in and inline schema out")
    res = client.actors.painter.example3(a="a", b=True, c=2)
    assert res.a == "a"
    assert res.b is False
    assert res.c == 2

    print("[3] Done")
    print("[4] inline schema for schema out with url")
    res = client.actors.painter.example4(wallet_in)
    assert res.result.addr == wallet_in.addr
    assert res.custom == "custom"
    print("[4] Done")

    print("[5] testing ping")
    s = j.clients.gedis.get("system", port=client.port, namespace="system", secret="123456")

    assert s.actors.system.ping().lower() == b"pong"

    assert client.actors.painter.echo("s") == b"s"

    print("[5] Done")

    print("**DONE**")
