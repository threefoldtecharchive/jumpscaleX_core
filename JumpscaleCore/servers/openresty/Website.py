from Jumpscale import j


JSConfigs = j.baseclasses.factory


class Website(j.baseclasses.object_config):
    """
    Website hosted in openresty
    """

    _SCHEMATEXT = """
        @url = jumpscale.openresty.website.1
        name* = (S)
        port = 80
        location =
        domain = ""
        path = ""

        """

    CONFIG = """
        server {
            {% if obj.domain %}
            server_name ~^(www\.)?{{obj.domain}}$;
            {% endif %}
            listen {{obj.port}};
            lua_code_cache on;
            default_type text/html;

            include vhosts/static.conf.loc;
            include vhosts/websocket.conf.loc;
            include vhosts/docsites.conf.loc;

            location /{{obj.location}} {
                root {{obj.path}};
            }

        }

        """

    def configure(self, config=None):
        """
        if config none then will use self.CONFIG

        config is a server config file of nginx (in text format)

        see `CONFIG` for an example.

        can use template variables with obj...  (obj is this obj = self)


        :param config:
        :return:
        """
        if not config:
            config = self.CONFIG
        if not config and self.port == 80 and self.domain == "":
            raise j.exceptions.Value("port or domain needs to be set")

        r = j.tools.jinja2.template_render(text=self.CONFIG, obj=self)
        j.sal.fs.writeFile("%s/servers/%s.conf" % (self._parent._parent._web_path, self.name), r)


class Websites(j.baseclasses.factory):

    _CHILDCLASS = Website
