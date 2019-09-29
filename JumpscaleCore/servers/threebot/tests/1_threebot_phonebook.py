from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.threebot.test(name="threebot_phonebook")'
    :return:
    """

    # add an actor

    cl = self.client

    nacl_test = j.data.nacl.get(name="test", configure_if_needed=True)

    r = cl.actors.phonebook.name_register(name="kristof.gouna2", pubkey=nacl_test.verify_key_hex)
    assert r.id

    # not such a good testthere is better in j.tools.threebot

    self._log_info("3bot worked")
