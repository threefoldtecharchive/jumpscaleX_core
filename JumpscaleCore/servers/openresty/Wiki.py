from Jumpscale import j


JSConfigs = j.baseclasses.objects_config_bcdb


class Wiki(j.baseclasses.object_config):
    """
    Website hosted in openresty
    """

    _SCHEMATEXT = """
        @url = jumpscale.openresty.wiki.1
        name* = (S)
        port = 80
        location =
        domain = ""
        giturl = ""
        branch = "master"

        """

    CONFIG = """
        server {
            {% if obj.domain %}
            server_name ~^(wiki\.)?{{obj.domain}}$;
            {% endif %}
            listen {{obj.port}};
            lua_code_cache on;

            include vhosts/static.conf.loc;
            include vhosts/websocket.conf.loc;
            include vhosts/gdrive.conf.loc;

            location / {
                set $name '{{obj.name}}';
                default_type text/html;
                content_by_lua_block {
                    require("lapis").serve("applications.wiki");
                }
            }
        }

        server {
            {% if obj.domain %}
            server_name ~^(wiki\.)?{{obj.domain}}$;
            {% endif %}
            listen {{obj.port}};
            lua_code_cache on;

            include vhosts/static.conf.loc;
            include vhosts/websocket.conf.loc;
            include vhosts/gdrive.conf.loc;

            location / {
                set $name '{{obj.name}}_dev';
                default_type text/html;
                content_by_lua_block {
                    require("lapis").serve("applications.wiki");
                }
            }
        }
        """

    def _init(self, **kwargs):
        self.update(pull=False)

    @property
    def docsite_path(self):
        return j.clients.git.getGitRepoArgs(self.giturl)[-3]

    def generate(self, pull=True):
        try:
            if not j.sal.fs.exists(self.docsite_path):
                raise j.exceptions.Base("%s does not exists, cannot generate docs from ")

            docs_path = "{}/docs".format(self.docsite_path)
            doc_site = j.tools.markdowndocs.load(docs_path, name=self.name, pull=pull)
            doc_site.write()
        except Exception as e:
            self._log_warning(e)

    def write_config(self):
        r = j.tools.jinja2.template_render(text=self.CONFIG, obj=self)
        j.sal.fs.writeFile("%s/servers/wiki_%s.conf" % (self._parent._parent._web_path, self.name), r)

    def update(self, pull=True, generate=False):
        """
        update content from source
        :param pull: means will update content from github
        :param docsgenerate: means will run the docsite generate, can take a while
        :return:
        """
        if pull:
            j.clients.git.pullGitRepo(self.giturl, branch=self.branch, dest=self.docsite_path)
        if generate:
            self.generate()
            self.write_config()


class Wikis(j.baseclasses.objects_config_bcdb):

    _CHILDCLASS = Wiki
