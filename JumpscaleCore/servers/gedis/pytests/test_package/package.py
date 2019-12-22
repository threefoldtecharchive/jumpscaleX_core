from Jumpscale import j


class Package(j.baseclasses.threebot_package):
    def start(self):
        self.openresty.configure()

        # get our main webserver
        for port in (443, 80):
            website = self.openresty.get_from_port(port)

            # PROXY for gedis HTTP
            locations = website.locations.get(name=f"test_package_locations_{port}")

            path = "/sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/servers/gedis/pytests/test_package/static/"
            location = locations.locations_static.new()
            location.name = "test_package"
            location.path_url = "/test_package/"
            location.path_location = path

            locations.save()

            website.configure()
