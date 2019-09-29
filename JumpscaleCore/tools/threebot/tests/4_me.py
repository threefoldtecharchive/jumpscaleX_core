from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.tools.threebot.test(name="me")'

    before you can execute this one:
    kosmos 'j.servers.threebot.test(name="onlystart")'
    needs to have been done, otherwise the threebot actors are not deployed on the server

    """

    self.explorer.actors.package_manager.package_add(
        "threebot_phonebook",
        git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/phonebook",
    )

    # need to make sure to reload the client, because we added a package
    self.explorer._client.reload()

    nacl1 = j.data.nacl.get(name="test_client")
    nacl2 = j.data.nacl.get(name="test_server")

    # name needs to correspond with the nacl name, this is your pub/priv key pair
    threebot_me_client = j.tools.threebot.init_my_threebot(
        myidentity="test_client", name="test_client", email=None, description=None, ipaddr="localhost"
    )
    threebot_me_server = j.tools.threebot.init_my_threebot(
        myidentity="test_server", name="test_server", email=None, description=None, ipaddr="localhost"
    )

    # lets now simulate the data flows & the encryption

    to_send = threebot_me_client.data_send_serialize(threebot_me_server.tid, {"a": 1})

    usable_data = threebot_me_server.data_received_unserialize(threebot_me_client.tid, to_send)

    back_over_wire = threebot_me_server.data_send_serialize(threebot_me_client.tid, usable_data)
    assert back_over_wire != to_send

    usable_data2 = threebot_me_client.data_received_unserialize(threebot_me_server.tid, back_over_wire)

    j.shell()
