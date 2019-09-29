from Jumpscale import j
from io import BytesIO
import binascii


def main(self):
    """
    kosmos -p 'j.servers.gedis.test("threebot_redis_registration")'
    """

    ####THREEBOT REGISTRATION

    phonebook = j.threebot.package.phonebook.client_get()

    if j.sal.nettools.tcpPortConnectionTest("www.google.com", 443):
        phonebook.actors.phonebook.wallet_create("test")

    j.data.nacl.configure(name="client_test", generate=True, interactive=False)
    client_nacl = j.data.nacl.get(name="client_test")

    cl = j.clients.redis.get(port=8901)

    def register_threebot_redis():

        cl.execute_command("config_format", "json")

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

        cl.execute_command("config_format", "json")

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

    print("**DONE**")
