from Jumpscale import j

skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/502")
def test_threebot_phonebook():
    """
    kosmos 'j.servers.threebot.test(name="threebot_phonebook")'
    :return:
    """

    # add an actor

    cl = j.servers.threebot.client

    j.me.configure(name="test", ask=False, reset=True)
    nacl_test = j.myidentities.get(name="test").encryptor
    # nacl_test = j.data.nacl.get(name="test", configure_if_needed=True)

    r = cl.actors.phonebook.name_register(name="kristof.gouna2", pubkey=nacl_test.verify_key)
    assert r.id

    # not such a good testthere is better in j.tools.threebot

    j.servers.threebot._log_info("3bot worked")
