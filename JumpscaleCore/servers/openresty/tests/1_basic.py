from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.threebot.test(name="basic")'
    :return:
    """

    server = j.servers.openresty.get("test")
    server.configure()
    website = server.websites.get("test2")
    website.configure()
    server.start()
    website.locations.get("test")