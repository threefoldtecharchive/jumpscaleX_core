from Jumpscale import j


JSConfigs = j.baseclasses.object_config_collection


class Location(j.baseclasses.object_config):
    """
    Website hosted in openresty
    This is port / hostname combination

    it will include locations from

    /sandbox/cfg/

    """

    _SCHEMATEXT = """
        @url = jumpscale.openresty.location
        name* = (S)
        use_jumpscale_weblibs = true (B)
        path = "/sandbox/var/web/default"
        locations = (LO) !jumpscale.openresty.location
        locations_proxy = (LO) !jumpscale.openresty.location_proxy
        locations_lapis = (LO) !jumpscale.openresty.location_lapis
        locations_custom = (LO) !jumpscale.openresty.location_custom
        
        @url = jumpscale.openresty.location
        path_url = "/sites/"
        path_location = "{{obj.path_webserver_default}}"
        
        @url = jumpscale.openresty.location_proxy
        name = "" (S)
        ipaddr_dest = (S)
        port_dest = (I)
        type = "http,websocket" (E)  
        
        @url = jumpscale.openresty.location_lapis
        name = ""
        path_url = ""
        path_location = ""
        
        @url = jumpscale.openresty.location_custom
        name = ""
        config = ""

        """

    CONFIG_LOCATION = """
          location {{obj.path_url}}{
            root {{obj.path_location}}/;
          }              

        """

    CONFIG_LAPIS = """
          location {{location.path_url}} {
            content_by_lua_block {
                require("lapis").serve("app")
            }
          }

        """

    CONFIG_PROXY = """
        {% if obj.proxy_type == 'websocket' %}
        location /{{location.path_url}} {
          proxy_pass http://{{location.ipaddr_dest}}:{{location.port_dest}};
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "Upgrade";
        }
        {% else %}    
        location /{{location.path_url}} {
          proxy_pass http://{{location.ipaddr_dest}}:{{location.port_dest}}/;
        }
        {% endif %}
        """

    CONFIG_WEBSOCKET_PROXY = """
        """  #

    # needs to be on level of servers in nginx and it is needed to get to websocket backend corresponds with proxy pass above
    # have to write this as server config in parent of this location
    CONFIG_UPSTREAM_WEBSOCKET = """
        upstream websocket_backend {
            server {{obj.ipaddr_dest}}:{{obj.port_dest}};
        }

    """

    @property
    def path_cfg_dir(self):
        return "%s/locations" % (self._parent._parent.path_cfg_dir)

    def path_cfg_get(self, name):
        return "%s/%s.conf" % (self.path_cfg_dir, name)

    @property
    def path_web(self):
        return self._parent._parent.path_web

    @property
    def path_web_default(self):
        return self._parent._parent.path_web_default

    def configure(self):
        """
        in the location obj: config is a server config file of nginx (in text format)
        can use template variables with obj...  (obj is this obj = self, location object is the sub obj)


        :param config:
        :return:
        """
        j.sal.fs.createDir(self.path_cfg_dir)

        for location in self.locations:
            content = j.tools.jinja2.template_render(text=self.CONFIG_LOCATION, obj=self, location=location)
            j.sal.fs.writeFile(self.path_cfg_get(location.name), content)

        for location in self.locations_proxy:
            content = j.tools.jinja2.template_render(text=self.CONFIG_PROXY, obj=self, location=location)
            j.sal.fs.writeFile(self.path_cfg_get(location.name), content)

        for location in self.locations_lapis:
            if location.path_location == "":
                location.path_location = self.path_location
            content = j.tools.jinja2.template_render(text=self.CONFIG_LAPIS, obj=self, location=location)
            j.sal.fs.writeFile(self.path_cfg_get(location.name), content)

        for location in self.locations_custom:
            j.sal.fs.writeFile(self.path_cfg_get(location.name), location.config)

    def configure_threebot(self):
        self.locations_lapis.new()
        c = self.locations_proxy.new()
        c.type = "websocket"
        c = self.locations.new()


class Locations(j.baseclasses.object_config_collection):

    _CHILDCLASS = Location
