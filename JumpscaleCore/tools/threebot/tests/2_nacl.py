from Jumpscale import j


def test_nacl():
    """
    to run:

    kosmos 'j.tools.threebot.test(name="nacl")'

    """

    # simulate I am remote threebot
    client_nacl = j.data.nacl.get(name="client_test")
    server_nacl = j.data.nacl.default  # (the one we have)

    server_tid = j.tools.threebot.me.default.tid
    client_tid = 99

    S = """
    @url = tools.threebot.test.schema
    name** = "aname"
    description = "something"
    """
    schema = j.data.schema.get_from_text(S)
    jsxobject = schema.new()

    j.tools.threebot._nacl = client_nacl

    ddict = j.baseclasses.dict()
    ddict["a"] = 2
    data = [True, 1, [1, 2, "a"], jsxobject, "astring", ddict]

    serialized = j.tools.threebot._serialize(data)
    unserialized = j.tools.threebot._unserialize(serialized)
    # test that the serialization works

    assert data == unserialized

    print("****client key:%s" % j.tools.threebot._nacl.public_key_hex)

    # it should encrypt for server_nacl.public_key_hex and sign with client_nacl
    data_send_over_wire = j.tools.threebot._serialize_sign_encrypt(data, pubkey_hex=server_nacl.public_key_hex)

    # client send the above to server

    # now we are server
    j.tools.threebot._nacl = server_nacl
    print("****server key:%s" % j.tools.threebot._nacl.public_key_hex)
    # server just returns the info

    # it should decrypt with server_nacl.public_key_hex and verify sign against client_nacl
    data_readable_on_server = j.tools.threebot._deserialize_check_decrypt(
        data_send_over_wire, verifykey_hex=client_nacl.verify_key_hex
    )
    # data has now been verified with pubkey of client

    assert data_readable_on_server == [True, 1, [1, 2, "a"], jsxobject, "astring", ddict]

    # lets now return the data to the client

    data_send_over_wire_return = j.tools.threebot._serialize_sign_encrypt(data, pubkey_hex=client_nacl.public_key_hex)

    # now we are client
    j.tools.threebot._nacl = client_nacl
    # now on client we check
    data_readable_on_client = j.tools.threebot._deserialize_check_decrypt(
        data_send_over_wire_return, verifykey_hex=server_nacl.verify_key_hex
    )

    # did full roundtrip
    assert data_readable_on_client == data

    # back to normal
    j.tools.threebot._nacl = server_nacl
    j.tools.threebot.me.default.tid = server_tid

    j.tools.threebot._log_info("TEST NACL DONE")
    return "OK"
