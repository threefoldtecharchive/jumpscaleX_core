from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.threebot.test(name="threebot")'
    :return:
    """

    # add an actor

    cl = self.client

    u = cl.actors.phonebook.register(name="kristof.gouna", email="kristof@test.com", pubkey="aaaaa", signature="bbbbb")

    u2 = cl.actors.phonebook.get(user_id=None, name="kristof.gouna")
    u3 = cl.actors.phonebook.get(user_id=None, email="kristof@test.com")

    self._log_info("ThreeBot worked")
