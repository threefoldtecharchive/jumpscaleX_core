from Jumpscale import j


def main(self):
    """
    kosmos -p 'j.servers.openresty.test(name="http_proxy")'
    kosmos 'j.servers.openresty.test(name="http_proxy")'
    :return:
    """

    server = j.servers.openresty.get("test")
    server.install(reset=True)
    server.configure()
    website = server.websites.get("test")
    website.ssl = False
    website.port = 8080
    locations = website.locations.get("original")

    website_location = locations.locations_static.new()
    website_location.name = "home"
    website_location.path_url = "/"
    website_location.path_location = f"{self._dirpath}/examples/website/"

    locations.configure()
    website.configure()

    website = server.websites.get("test2")
    website.ssl = False
    locations = website.locations.get("proxied")
    proxy_location = locations.locations_proxy.new()
    proxy_location.name = "proxy1"
    proxy_location.path_url = "/"
    proxy_location.ipaddr_dest = "0.0.0.0"
    proxy_location.port_dest = "8080"
    proxy_location.scheme = "http"
    locations.configure()
    website.configure()

    server.start()

    static_content = j.clients.http.get("http://0.0.0.0/")
    assert static_content == "<html>\nHello from static!\n</html>\n"
