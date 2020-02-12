from Jumpscale import j



def test_basic():
    """
    kosmos -p 'j.servers.openresty.test(name="basic")'
    kosmos 'j.servers.openresty.test(name="basic")'
    :return:
    """

    server = j.servers.openresty.get("test")
    server.stop()

    server.install(reset=True)
    server.configure()
    website = server.websites.get("test1")
    website.ssl = False
    locations = website.locations.get("home")

    website_location = locations.locations_static.new()
    website_location.name = "home"
    website_location.path_url = "/website"
    website_location.path_location = f"{j.servers.openresty._dirpath}/examples/website/"

    lapis_location = locations.locations_lapis.new()
    lapis_location.name = "apps"
    lapis_location.path_url = "/"
    lapis_location.path_location = f"{j.servers.openresty._dirpath}/examples/lapis"

    static_location = locations.locations_static.new()
    static_location.name = "static"
    static_location.path_url = "/static"
    static_location.path_location = f"{j.servers.openresty._dirpath}/web_resources/static"
    static_location.use_jumpscale_weblibs = True

    locations.configure()
    website.configure()
    server.start()

    lapis_content = j.clients.http.get("http://0.0.0.0/")
    assert (
        lapis_content
        == '<!DOCTYPE HTML><html lang="en"><head><title>Lapis Page</title></head><body>Hello from lapis!</body></html>'
    )

    static_content = j.clients.http.get("http://0.0.0.0/website/")
    assert static_content == "<html>\nHello from static!\n</html>\n"

    server.cleanup()
    server.stop()
    server.delete()
