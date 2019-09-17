from Jumpscale import j
from io import BytesIO
import binascii


def main(self):
    """
    kosmos -p 'j.servers.gedis.test("redis_interface")'
    """

    r0 = self.client.actors.ibiza_actor.info("aaa")
    assert r0 == b"aaa"

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

    #### LETS NOW TEST WITH ENCRYPTION

    # phonebook = j.threebot.package.phonebook.client_get()
    # phonebook.actors.phonebook.wallet_create("test")

    j.data.nacl.configure(name="client_test", generate=True, interactive=False)
    client_nacl = j.data.nacl.get(name="client_test")
    myname = "test.ibiza"

    data_return_json = cl.execute_command(
        "default.phonebook.name_register", j.data.serializers.json.dumps({"name": myname})
    )

    data = {
        "name": myname,
        "email": "something@threefold.com",
        "ipaddr": "212.3.247.26",
        "description": "",
        "pubkey": client_nacl.verify_key_hex,
    }

    def sign(nacl, *args):
        buffer = BytesIO()
        for item in args:
            if isinstance(item, str):
                item = item.encode()
            elif isinstance(item, bytes):
                pass
            else:
                raise RuntimeError()
            buffer.write(item)
        payload = buffer.getvalue()
        signature = nacl.sign(payload)
        return binascii.hexlify(signature).decode()

    data2 = j.data.serializers.json.dumps(data)
    signature = sign(client_nacl, data["name"], data["email"], data["ipaddr"], data["description"], data["pubkey"])

    data_return_json = cl.execute_command("default.phonebook.record_register", data2, signature)

    data2 = j.data.serializers.json.dumps({"name": myname, "sender_signature_hex": sender_signature_hex})
    data3 = cl.execute_command("default.phonebook.name_register", data2)

    j.shell()

    print("**DONE**")
