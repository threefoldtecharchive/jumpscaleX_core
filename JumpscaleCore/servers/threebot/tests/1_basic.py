from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.threebot.test(name="basic")'
    :return:
    """

    # add an actor

    cl = self.client

    s = j.data.schema.get_from_url("tfgrid.node.2")
    node = s.new()
    node.node_id = "111"
    node2 = cl.actors.nodes.add(node)

    node3 = cl.actors.nodes.add(node)

    ns = cl.actors.nodes.list()

    r = cl.actors.farms.list()

    u = cl.actors.phonebook.register(name="kristof.gouna", email="kristof@test.com", pubkey="aaaaa", signature="bbbbb")

    u2 = cl.actors.phonebook.get(user_id=None, name="kristof.gouna")
    u3 = cl.actors.phonebook.get(user_id=None, email="kristof@test.com")

    self._log_info("ThreeBot worked")
