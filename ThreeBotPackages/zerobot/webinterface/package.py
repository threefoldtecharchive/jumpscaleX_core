from Jumpscale import j


class Package(j.baseclasses.threebot_package):
    def setup_locations(self):
        """
        ports & paths used for threebotserver
        see: {DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/docs/3Bot/web_environment.md
        will start bottle server web interface which include (gedis http interface, gedis websocket interface and
        bcdbfs web server)
        endpoints:
        "/web/gedis/http"       >    gedis htto interface
        "/web/gedis/websocket"  >    gedis websocket interface
        "/web/bcdbfs"           >    bcdbfs web server
        "/weblibs"              >    static jumpscale weblibs files
        """

        self.openresty.configure()

        # get our main webserver
        for port in (443, 80):
            website = self.openresty.get_from_port(port)

            # PROXY for gedis HTTP
            locations = website.locations.get(name=f"webinterface_locations_{port}")

            gedis_bcdbfs_proxy_location = locations.locations_proxy.new()
            gedis_bcdbfs_proxy_location.name = "gedis_bcdbfs"
            gedis_bcdbfs_proxy_location.path_url = "~* ^/(3git|gedis|bcdbfs|auth|wiki)"
            gedis_bcdbfs_proxy_location.ipaddr_dest = "127.0.0.1"
            gedis_bcdbfs_proxy_location.port_dest = 9999
            gedis_bcdbfs_proxy_location.path_dest = ""
            gedis_bcdbfs_proxy_location.type = "http"
            gedis_bcdbfs_proxy_location.scheme = "http"

            chat_wiki_proxy_location = locations.locations_proxy.new()
            chat_wiki_proxy_location.name = "chat_wiki_actors"
            chat_wiki_proxy_location.path_url = "~* ^/(.*)/(.*)/(chat|wiki|actors)"
            chat_wiki_proxy_location.ipaddr_dest = "127.0.0.1"
            chat_wiki_proxy_location.port_dest = 9999

            url = "https://github.com/threefoldtech/jumpscaleX_weblibs"
            weblibs_path = j.clients.git.getContentPathFromURLorPath(url, pull=False)
            weblibs_location = locations.locations_static.new()
            weblibs_location.name = "weblibs"
            weblibs_location.path_url = "/weblibs"
            weblibs_location.path_location = f"{weblibs_path}/static"

            chat_static_location = locations.locations_static.new()
            chat_static_location.name = "chat_static"
            chat_static_location.path_url = "/staticchat"
            chat_static_location.path_location = f"{self._dirpath}/static"

            wiki_static_location = locations.locations_static.new()
            wiki_static_location.name = "wiki_static"
            wiki_static_location.path_url = "/staticwiki"
            wiki_static_location.path_location = f"{self._dirpath}/static"

            website.configure()

    def start(self):

        # add the main webapplication

        self.setup_locations()

        from threebot_packages.zerobot.webinterface.bottle.rooter import app_with_session

        self.gevent_rack.bottle_server_add(name="bottle_web_interface", port=9999, app=app_with_session, websocket=True)
        # self.gevent_rack.webapp_root = webapp
