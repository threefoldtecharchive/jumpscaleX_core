from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.tools.threebot.test(name="nacl")'

    """

    # simulate I am remote threebot
    j.data.nacl.configure(name="client_test", generate=True, interactive=False)
    client_nacl = j.data.nacl.get(name="client_test")
    server_nacl = j.data.nacl.default  # (the one we have)

    server_tid = j.core.myenv.config["THREEBOT_ID"]
    client_tid = 99

    S = """
    @url = tools.threebot.test.schema
    name** = "aname"
    description = "something" 
    """
    schema = j.data.schema.get_from_text(S)
    jsxobject = schema.new()

    self._nacl = client_nacl

    ddict = j.baseclasses.dict()
    ddict["a"] = 2
    data = [True, 1, [1, 2, "a"], jsxobject, "astring", ddict]

    serialized = self.serialize(data)
    unserialized = self.unserialize(serialized)
    # test that the serialization works

    assert data == unserialized

    data_send_over_wire = self.serialize_sign_encrypt(data, pubkey_hex=server_nacl.public_key_hex)

    # client send the above to server

    # now we are server
    self._nacl = server_nacl

    # server just returns the info

    data_readable_on_server = self.deserialize_check_decrypt(data_send_over_wire, pubkey_hex=client_nacl.public_key_hex)
    # data has now been verified with pubkey of client

    j.shell()

    assert data_readable_on_server == [True, 1, [1, 2, "a"], jsxobject, "astring"]

    # lets now return the data to the client

    data_send_over_wire_return = self.serialize_sign_encrypt(data, pubkey_hex=client_nacl.pubkey)

    # now we are client
    self._nacl = client_nacl
    # now on client we check
    data_readable_on_client = self.deserialize_check_decrypt(data_send_over_wire_return, pubkey_hex=server_nacl.pubkey)

    # back to normal
    self._nacl = server_nacl
    j.core.myenv.config["THREEBOT_ID"] = server_tid

    self._log_info("TEST NACL DONE")
    return "OK"
