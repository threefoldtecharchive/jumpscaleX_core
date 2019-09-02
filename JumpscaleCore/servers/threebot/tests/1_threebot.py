from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.threebot.test(name="threebot")'
    :return:
    """

    # add an actor

    cl = self.client

    u = cl.actors.phonebook.register(
        name="kristof.gouna2", email="kristof@test2.com", pubkey="aaaaa", signature="bbbbb"
    )

    u2 = cl.actors.phonebook.get(user_id=None, name="kristof.gouna2")
    u3 = cl.actors.phonebook.get(user_id=None, email="kristof@test2.com")

    j.shell()

    self._log_info("ThreeBot worked")
