from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.tools.threebot.test(name="me")'

    """

    # a threebotme is a local threebot definition, it holds your pubkey, ...
    # this returns 2 test nacl sessions & threebot definiions for a fake client & threebotserver
    nacl1, nacl2, threebot_me_client, threebot_me_server = j.tools.threebot.test_register_nacl_threebots()

    # std you should use j.data.threebot.me.default as your local connection

    # lets now simulate the data flows & the encryption

    tid, data3, signature = threebot_me_client.data_send_serialize(threebot_me_server.tid, {"a": 1})
    assert len(signature) == 128
    assert tid == threebot_me_server.tid

    usable_data = threebot_me_server.data_received_unserialize(threebot_me_client.tid, signature=signature, data=data3)

    assert usable_data == {"a": 1}

    client_tid, back_over_wire, signature = threebot_me_server.data_send_serialize(threebot_me_client.tid, usable_data)
    assert back_over_wire != data3

    usable_data2 = threebot_me_client.data_received_unserialize(
        threebot_me_server.tid, back_over_wire, signature=signature
    )

    assert usable_data2 == {"a": 1}

    j.tools.timer.start("encrypt and decrypt cycle for a non serialized object")
    nr = 1000
    for x in range(nr):
        tid, data3, signature = threebot_me_client.data_send_serialize(threebot_me_server.tid, {"a": 1})
        usable_data = threebot_me_server.data_received_unserialize(
            threebot_me_client.tid, signature=signature, data=data3
        )
    res = j.tools.timer.stop(nr)

    # on my laptop had 3000 per sec
    assert res > 500

    print("TEST OK")
