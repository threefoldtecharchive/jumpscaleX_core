from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.tools.threebot.test(name="me")'

    """
    nacl1 = j.data.nacl.configure(name="client_test")
    nacl2 = j.data.nacl.configure(name="client_test2")
    client = j.tools.threebot.init(
        myidentity="client_test", name="client_test", email=None, description=None, ipaddr="", interactive=False
    )
    server = j.tools.threebot.init(
        myidentity="client_test2", name="client_test2", email=None, description=None, ipaddr="", interactive=False
    )

    j.shell()
