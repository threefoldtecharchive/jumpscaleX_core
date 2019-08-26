from Jumpscale import j

JSConfigs = j.baseclasses.object_config_collection


class ReverseProxy(j.baseclasses.object_config):
    """
    Reverse Proxy using openresty server
    """

    _SCHEMATEXT = """
        @url = jumpscale.openresty.reverseproxy.1
        name* = (S)
        port_source = 80
        ipaddr_dest = "127.0.0.1"
        port_dest = 80
        location =
        domain = ""
        proxy_type = 'http' # websocket, tcp, http
        """

    HTTP_CONFIG = """
        {% if obj.proxy_type == 'websocket' %}
        upstream websocket_backend {
            server {{obj.ipaddr_dest}}:{{obj.port_dest}};
        }
        {% endif %}

        server {
            listen {{obj.port_source}} ssl;
            listen [::]:{{obj.port_source}} ssl;
            ssl_certificate_by_lua_block {
                auto_ssl:ssl_certificate()
            }
            ssl_certificate /sandbox/cfg/ssl/resty-auto-ssl-fallback.crt;
            ssl_certificate_key /sandbox/cfg/ssl/resty-auto-ssl-fallback.key;

            {% if obj.domain %}
            server_name ~^(www\.)?{{domain}}$;
            {% endif %}

            location /{{obj.location}} {
              {% if obj.proxy_type == 'http'%}
              proxy_pass http://{{obj.ipaddr_dest}}:{{obj.port_dest}}/;

              {% elif obj.proxy_type == 'websocket' %}
              proxy_pass http://websocket_backend;
              proxy_http_version 1.1;
              proxy_set_header Upgrade $http_upgrade;
              proxy_set_header Connection "Upgrade";
              {% endif %}
            }
        }
        """

    # @TODO : certificates needs to be fixed
    TCP_CONFIG = """
        stream {
            server {
                listen {{obj.port_source}};
                listen [::]:{{obj.port_source}};
                proxy_pass backend;
            }
            upstream backend {
                server {{obj.ipaddr_dest}}:{{obj.port_dest}};
            }
        }
        """

    def configure(self):
        """

        when initializing this class it will already write the config, but this method can be called to rewrite it

        """
        j.sal.fs.createDir("%s/servers/http_proxy" % self._parent._parent._web_path)
        j.sal.fs.createDir("%s/servers/tcp_proxy" % self._parent._parent._web_path)

        if self.proxy_type in ["http", "websocket"]:
            r = j.tools.jinja2.template_render(text=self.HTTP_CONFIG, obj=self)
            j.sal.fs.writeFile("%s/servers/http_proxy/proxy_%s.conf" % (self._parent._parent._web_path, self.name), r)
        else:  # TCP proxy_type = 'tcp'
            r = j.tools.jinja2.template_render(text=self.TCP_CONFIG, obj=self)
            j.sal.fs.writeFile("%s/servers/tcp_proxy/proxy_%s.conf" % (self._parent._parent._web_path, self.name), r)


class ReverseProxies(j.baseclasses.object_config_collection):

    _CHILDFACTORY_CLASS = ReverseProxy
