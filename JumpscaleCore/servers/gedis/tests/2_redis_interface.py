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

    ####THREEBOT REGISTRATION

    # phonebook = j.threebot.package.phonebook.client_get()
    # phonebook.actors.phonebook.wallet_create("test")

    j.data.nacl.configure(name="client_test", generate=True, interactive=False)
    client_nacl = j.data.nacl.get(name="client_test")

    def register_threebot_redis():

        # get a nacl config (to act as a virtual person)
        myname = "test.ibiza"

        data_return_json = cl.execute_command(
            "default.phonebook.name_register",
            j.data.serializers.json.dumps({"name": myname, "pubkey": client_nacl.verify_key_hex}),
        )

        data_return = j.data.serializers.json.loads(data_return_json)

        assert data_return["pubkey"] == client_nacl.verify_key_hex
        assert data_return["name"] == myname

        data = {
            "tid": data_return["id"],
            "name": data_return["name"],
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
                elif isinstance(item, int):
                    item = str(item).encode()
                elif isinstance(item, bytes):
                    pass
                else:
                    raise RuntimeError()
                buffer.write(item)
            payload = buffer.getvalue()
            print(payload)
            signature = nacl.sign(payload)
            return binascii.hexlify(signature).decode()

        # we sign the different records to come up with the right 'sender_signature_hex'
        sender_signature_hex = sign(
            client_nacl, data["tid"], data["name"], data["email"], data["ipaddr"], data["description"], data["pubkey"]
        )
        data["sender_signature_hex"] = sender_signature_hex
        data2 = j.data.serializers.json.dumps(data)
        data_return_json = cl.execute_command("default.phonebook.record_register", data2)
        data_return = j.data.serializers.json.loads(data_return_json)

        print(data)

        return data_return

    def query_threebot_redis(tid):

        myname = "test.ibiza"

        data2 = j.data.serializers.json.dumps({"name": myname})
        res_json = cl.execute_command("default.phonebook.get", data2)

        threebot_info3 = j.data.serializers.json.loads(res_json)

        data2 = j.data.serializers.json.dumps({"tid": tid})
        res_json = cl.execute_command("default.phonebook.get", data2)

        threebot_info4 = j.data.serializers.json.loads(res_json)

        assert threebot_info3 == threebot_info4

        # verify the data (is same logic as above in register threebot, to see if record is valid)
        rc = j.data.nacl.payload_verify(
            threebot_info4["id"],
            threebot_info4["name"],
            threebot_info4["email"],
            threebot_info4["ipaddr"],
            threebot_info4["description"],
            threebot_info4["pubkey"],
            verifykey=threebot_info4["pubkey"],
            signature=threebot_info4["signature"],
            die=True,
        )

        return threebot_info4

    threebot_info = register_threebot_redis()
    threebot_info2 = query_threebot_redis(threebot_info["id"])
    assert threebot_info == threebot_info2

    #### LETS NOW TEST WITH ENCRYPTION

    # will register a threebot test.test & dummy.myself
    # returns the 2 nacls used in this test
    nacl1, nacl2, threebot1, threebot2 = j.clients.threebot.test()

    j.shell()

    print("**DONE**")
