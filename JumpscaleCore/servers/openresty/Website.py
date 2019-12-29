from .Location import Locations
from Jumpscale import j


class Website(j.baseclasses.factory_data):
    """
    Website hosted in openresty
    This is port / hostname combination

    it will include locations from

    {DIR_BASE}/cfg/

    """

    _CHILDCLASSES = [Locations]

    _SCHEMATEXT = """
        @url = jumpscale.openresty.website
        name** = (S)
        port = 80 (I)
        ssl = True (B)
        domain = ""
        path = ""
        """

    CONFIG = """

    {% if website.ssl %}
    server {
      {% if website.domain %}
      server_name ~^(www\.)?{{website.domain}}$;
      {% endif %}
      listen {{website.port}} ssl;
      ssl_certificate_by_lua_block {
        auto_ssl:ssl_certificate()
      }
      ssl_certificate {DIR_BASE}/cfg/ssl/resty-auto-ssl-fallback.crt;
      ssl_certificate_key {DIR_BASE}/cfg/ssl/resty-auto-ssl-fallback.key;
      default_type text/html;

      include {{website.path_cfg_dir}}/{{website.name}}_locations/*.conf;
      include vhosts/*.conf.loc;
    }
    {% else %}
    server {
      {% if website.domain %}
      server_name ~^(www\.)?{{website.domain}}$;
      {% endif %}
      listen {{website.port}};

      default_type text/html;
      include {{website.path_cfg_dir}}/{{website.name}}_locations/*.conf;
      include vhosts/*.conf.loc;
    }

    {% endif %}

        """

    @property
    def path_cfg_dir(self):
        return f"{self._parent._parent.path_cfg_dir}/servers"

    @property
    def path_cfg(self):
        return f"{self.path_cfg_dir}/{self.name}.http.conf"

    @property
    def path_web(self):
        return self._parent._parent.path_web

    @property
    def path_web_default(self):
        return self._parent._parent.path_web_default

    def configure(self):
        """
        if config none then will use self.CONFIG

        config is a server config file of nginx (in text format)

        see `CONFIG` for an example.

        can use template variables with website...  (obj is this obj = self)


        :param config:
        :return:
        """

        j.sal.fs.createDir(self.path_cfg_dir)
        self.CONFIG = self.CONFIG.replace("{DIR_BASE}", j.dirs.BASEDIR)
        r = j.tools.jinja2.template_render(text=self.CONFIG, website=self)
        j.sal.fs.writeFile(self.path_cfg, r)

        for locationsconfigs in self.locations.find():
            locationsconfigs.configure()


class Websites(j.baseclasses.object_config_collection):

    _CHILDCLASS = Website
