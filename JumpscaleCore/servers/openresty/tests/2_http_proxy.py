import gevent
from Jumpscale import j




def test_http_proxy():
    """
    kosmos -p 'j.servers.openresty.test(name="http_proxy")'
    kosmos 'j.servers.openresty.test(name="http_proxy")'
    :return:
    """

    server = j.servers.openresty.get("test")
    server.stop()

    server.install(reset=True)
    server.configure()
    server.cleanup()
    server.start()

    website = server.websites.get("test")
    website.ssl = False
    website.port = 8080
    locations = website.locations.get("original")

    website_location = locations.locations_static.new()
    website_location.name = "home"
    website_location.path_url = "/"
    website_location.path_location = f"{j.servers.openresty._dirpath}/examples/website/"

    locations.configure()
    website.configure()

    locations = website.locations.get("proxied")
    proxy_location = locations.locations_proxy.new()
    proxy_location.name = "proxy1"
    proxy_location.path_url = "/app"
    proxy_location.ipaddr_dest = "0.0.0.0"
    proxy_location.port_dest = "8080"
    proxy_location.path_dest = "/"
    proxy_location.scheme = "http"
    locations.configure()
    website.configure()

    server.reload()

    gevent.sleep(1)
    static_content = j.clients.http.get("http://0.0.0.0:8080/app")
    assert static_content == "<html>\nHello from static!\n</html>\n"

    website.delete()
    server.cleanup()
    server.stop()
