from Jumpscale import j


class Package(j.baseclasses.threebot_package):
    def prepare(self):
        """
        is called at install time
        :return:
        """
        pass

    def start(self):
        """
        called when the 3bot starts
        :return:
        """
        server = self.openresty
        server.configure()

        from threebot_packages.zerobot.oauth2.bottle.Oauth2Bottle import app

        j.threebot.servers.gevent_rack.bottle_server_add(name="oauth", port=8523, app=app)
        for port in (443, 80):
            website = server.get_from_port(port=port)
            locations = website.locations.get(f"main_oauth2_{port}")

            proxy_location = locations.locations_proxy.new()
            proxy_location.name = "oauth"
            proxy_location.path_url = "/oauth"
            proxy_location.ipaddr_dest = "0.0.0.0"
            proxy_location.port_dest = 8523
            proxy_location.scheme = "http"
            locations.configure()
            website.configure()

    def stop(self):
        """
        called when the 3bot stops
        :return:
        """
        pass

    def uninstall(self):
        """
        called when the package is no longer needed and will be removed from the threebot
        :return:
        """
        # TODO: clean up bcdb ?
        pass
