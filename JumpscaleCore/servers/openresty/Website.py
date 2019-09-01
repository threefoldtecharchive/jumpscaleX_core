from Jumpscale import j


JSConfigs = j.baseclasses.object_config_collection
from .Location import Location


class Website(j.baseclasses.factory_data):
    """
    Website hosted in openresty
    This is port / hostname combination

    it will include locations from

    /sandbox/cfg/

    """

    _CHILDCLASSES = [Location]

    _SCHEMATEXT = """
        @url = jumpscale.openresty.website
        name* = (S)
        port = 80 (I)
        port_ssl = 443 (I)
        
        domain = ""
        path = ""

        """

    CONFIG = """
        
        {% if website.letsencrypt %}
        server {
          {% if website.domain %}
          server_name ~^(www\.)?{{website.domain}}$;
          {% endif %}
          listen {website.port_ssl} ssl;
          ssl_certificate_by_lua_block {
            auto_ssl:ssl_certificate()
          }
          ssl_certificate /sandbox/cfg/ssl/resty-auto-ssl-fallback.crt;
          ssl_certificate_key /sandbox/cfg/ssl/resty-auto-ssl-fallback.key;
          default_type text/html;
          
          include {{website.path_cfg_dir}}/locations/*.conf;
    
        }
    
        #also used by letsencrypt
        server {
          listen 127.0.0.1:8999;
          client_body_buffer_size 128k;
          client_max_body_size 128k;
    
          location / {
            content_by_lua_block {
              auto_ssl:hook_server()
            }
          }
        }
    
    
        server {
          listen {website.port};    
          include {{website.path_cfg_dir}}/locations/*.conf;
        }     
        
    {% else %}
    server {
      listen {website.port};

      default_type text/html;
      include {{website.path_cfg_dir}}/locations/*.conf;

    }
    {% endif %}           

        """

    @property
    def path_cfg_dir(self):
        return "%s/%s" % (self._parent._parent.path_cfg_dir, self.name)

    @property
    def path_cfg(self):
        return "%s/website.conf" % (self.path_cfg_dir)

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

        r = j.tools.jinja2.template_render(text=self.CONFIG, website=self)
        j.sal.fs.writeFile(self.path_cfg, r)


class Websites(j.baseclasses.object_config_collection):

    _CHILDCLASS = Website
