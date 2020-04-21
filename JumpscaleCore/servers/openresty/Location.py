from Jumpscale import j


JSConfigs = j.baseclasses.object_config_collection
TEMPLATES_PATH = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), "templates")
env = j.tools.jinja2.env_get(TEMPLATES_PATH)


def render_config_template(name, **kwargs):
    return env.get_template(f"{name}.conf").render(**kwargs)


class LocationsConfiguration(j.baseclasses.object_config):
    """
    Website hosted in openresty
    This is port / hostname combination

    it will include locations from

    {DIR_BASE}/cfg/

    """

    _SCHEMATEXT = """
        @url = jumpscale.openresty.location
        name** = (S)
        path = "/sandbox/var/web/default" (S)
        locations_static = (LO) !jumpscale.openresty.location_static
        locations_proxy = (LO) !jumpscale.openresty.location_proxy
        locations_lapis = (LO) !jumpscale.openresty.location_lapis
        locations_custom = (LO) !jumpscale.openresty.location_custom
        locations_spa = (LO) !jumpscale.openresty.location_static
        mother_id** = 0 (I)

        @url = jumpscale.openresty.location_static
        name = "" (S)
        path_url = "/"
        path_location = ""
        index = "index.html"
        use_jumpscale_weblibs = false (B)
        is_auth = false (B)
        force_https = false (B)
        is_admin = false (B)

        @url = jumpscale.openresty.location_proxy
        name = "" (S)
        path_url = ""
        ipaddr_dest = (S)
        port_dest = (I)
        path_dest = "" (S)
        type = "http,websocket" (E)
        scheme = "http,https,ws,wss" (E)
        is_auth = false (B)
        force_https = false (B)
        is_admin = false (B)

        @url = jumpscale.openresty.location_lapis
        name = ""
        path_url = ""
        path_location = ""
        is_auth = false (B)
        force_https = false (B)
        is_admin = false (B)

        @url = jumpscale.openresty.location_custom
        name = ""
        config = ""
        is_auth = false (B)
        force_https = false (B)
        is_admin = false (B)

        """
    WITH_THREEBOTCONNECT = j.core.myenv.config.get("THREEBOT_CONNECT", False)

    def get_location_proxy(self, new_location_name):
        return self.check_location_exists(self.locations_proxy, new_location_name)

    def get_location_static(self, new_location_name):
        return self.check_location_exists(self.locations_static, new_location_name)

    def get_location_lapis(self, new_location_name):
        return self.check_location_exists(self.locations_lapis, new_location_name)

    def get_location_spa(self, new_location_name):
        return self.check_location_exists(self.locations_spa, new_location_name)

    def get_location_custom(self, new_location_name):
        return self.check_location_exists(self.locations_custom, new_location_name)

    @property
    def path_cfg_dir(self):
        return f"{self._parent._parent.path_cfg_dir}/{self._parent._parent.name}_locations"

    def path_cfg_get(self, name):
        return f"{self.path_cfg_dir}/{name}.conf"

    @property
    def path_web(self):
        return self._parent._parent.path_web

    @property
    def path_web_default(self):
        return self._parent._parent.path_web_default

    def write_config(self, location, content=None):
        if not content:
            template_name = location._schema.url.split(".")[-1]
            content = render_config_template(template_name, obj=location)
        if not self.WITH_THREEBOTCONNECT:
            location.is_auth = False
        j.sal.fs.writeFile(self.path_cfg_get(location.name), content)

    def configure(self):
        """
        in the location obj: config is a server config file of nginx (in text format)
        can use template variables with obj...  (obj is this obj = self, location object is the sub obj)

        :return:
        """
        j.sal.fs.createDir(self.path_cfg_dir)

        for location in list(self.locations_static) + list(self.locations_spa):
            if not location.path_location.endswith("/"):
                location.path_location += "/"

            self.write_config(location)

        for location in self.locations_proxy:

            self.write_config(location)

        for location in self.locations_lapis:
            if location.path_location == "":
                location.path_location = self.path_location

            self.write_config(location)
            j.sal.process.execute("cd %s;moonc ." % location.path_location)

        for location in self.locations_custom:
            self.write_config(location, content=location.config)

    # Helper function
    @staticmethod
    def check_location_exists(locations_obj, new_location_name):
        # check if the location already exists or not
        location = [location for location in locations_obj if location.name == new_location_name]
        # if we found the location we return it else we create a new one
        if len(location) != 0:
            return location.pop()
        else:
            new_location = locations_obj.new()
            new_location.name = new_location_name
            return new_location


class Locations(j.baseclasses.object_config_collection):

    _CHILDCLASS = LocationsConfiguration

    def configure(self):
        for item in self.find():
            item.configure()
