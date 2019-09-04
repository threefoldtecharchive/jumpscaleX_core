from Jumpscale import j


def main(self):
    """
    kosmos -p 'j.servers.openresty.test(name="basic")'
    kosmos 'j.servers.openresty.test(name="basic")'
    :return:
    """

    server = j.servers.openresty.get("test")
    server.configure()
    website = server.websites.get("test2")
    website.configure()

    website.locations.get("test")

    server.start()
