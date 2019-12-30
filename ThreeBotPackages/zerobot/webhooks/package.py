from Jumpscale import j


class Package(j.baseclasses.threebot_package):
    def start(self):
        """
        called when the 3bot starts
        :return:
        """

        server = self.openresty
        server.configure()
        for port in (443, 80):
            website = server.get_from_port(port=port)
            locations = website.locations.get("main_webhooks")

            from threebot_packages.zerobot.webhooks.bottle.main import app

            self.gevent_rack.bottle_server_add(name="webhooks", port=8530, app=app)

            proxy_location = locations.locations_proxy.new()
            proxy_location.name = "webhooks"
            proxy_location.path_url = "/webhooks"
            proxy_location.ipaddr_dest = "0.0.0.0"
            proxy_location.port_dest = 8530
            proxy_location.scheme = "http"

            locations.configure()
            website.configure()
