from .ReverseProxy import ReverseProxies
from .Wiki import Wikis
from .Website import Websites
from Jumpscale import j

JSBASE = j.baseclasses.object

# WIKI_CONFIG_TEMPLATE = "templates/WIKI_CONF_TEMPLATE.conf"
# WEBSITE_CONFIG_TEMPLATE = "templates/WEBSITE_CONF_TEMPLATE.conf"
# WEBSITE_STATIC_CONFIG_TEMPLATE = "templates/WEBSITE_STATIC_CONF_TEMPLATE.conf"
# OPEN_PUBLISH_REPO = "https://github.com/threefoldtech/OpenPublish"


class OpenRestyServer(j.application.JSBaseConfigsConfigFactoryClass):
    """
    Factory for openresty
    """

    _CHILDCLASSES = [Websites, ReverseProxies]
    _SCHEMATEXT = """
           @url =  jumpscale.openresty.server.1
           name* = "default" (S)
           host = "127.0.0.1" (S)
           port = 80 (I)
           port_ssl = 443 (I)
           status = init,installed,ok (E)
           executor = tmux,corex (E)
           hardkill = false (b)
           state = "init,running,error,stopped,stopping,down,notfound" (E)
           corex_client_name = "default" (S)
           corex_id = (S)
           error = "" (S)
           time_start = (T)
           time_refresh = (T)
           time_stop = (T)
           """

    def _init(self, **kwargs):
        self._cmd = None
        self._web_path = "/sandbox/var/web/%s" % self.name
        j.sal.fs.createDir(self._web_path)

        self.executor = "tmux"

        self.install()

        if j.core.myenv.platform_is_linux:
            self.letsencrypt = True
        else:
            self.letsencrypt = True

        self.configure()

    def configure(self):
        r = j.tools.jinja2.template_render(path="%s/templates/nginx.conf" % self._dirpath, obj=self)
        j.sal.fs.writeFile("%s/nginx.conf" % self._web_path, r)

    def install(self, reset=False):
        """
        kosmos 'j.servers.openresty.default.install(reset=True)'
        :param reset:
        :return:
        """

        if reset or self.status not in ["ok", "installed"]:

            # get weblib
            url = "https://github.com/threefoldtech/jumpscale_weblibs"

            weblibs_path = j.clients.git.getContentPathFromURLorPath(url, pull=False)

            # copy the templates to the right location
            j.sal.fs.copyDirTree("%s/web_resources/" % self._dirpath, self._web_path)

            j.sal.fs.symlink(
                "%s/static" % weblibs_path, "{}/static/weblibs".format(self._web_path), overwriteTarget=True
            )

            # link individual files & create a directory TODO:*1
            lualib_dir = "/sandbox/openresty/lualib"
            if not j.sal.fs.exists(lualib_dir):
                j.sal.fs.createDir(lualib_dir)
            j.sal.fs.copyFile(
                "%s/web_resources/lualib/redis.lua" % self._dirpath, "/sandbox/openresty/lualib/redis.lua"
            )
            j.sal.fs.copyFile(
                "%s/web_resources/lualib/websocket.lua" % self._dirpath, "/sandbox/openresty/lualib/websocket.lua"
            )
            self.status = "installed"

            self.save()

    @property
    def startup_cmd(self):
        """
        lapis starts nginx.conf in the directory it is, thats why path is important
        :return:
        """
        if not self._cmd:
            # Start Lapis Server
            self._log_info("Starting Lapis Server")
            cmd = "lapis server"
            self._cmd = j.servers.startupcmd.get(
                name="lapis",
                cmd_start=cmd,
                path=self._web_path,
                ports=[self.port, self.port_ssl],
                process_strings_regex="^nginx",
                executor=self.executor,
            )
        return self._cmd

    def start(self, reset=False):
        """
        kosmos 'j.servers.openresty.default.start(reset=True)'
        kosmos 'j.servers.openresty.default.start(reset=False)'
        :return:
        """
        self.install(reset=reset)
        self.configure()
        # compile all 1 time to lua, can do this at each start
        j.sal.process.execute("cd %s;moonc ." % self._web_path)
        if reset:
            self.startup_cmd.stop()
        if self.startup_cmd.is_running():
            self.reload()
        else:
            self.startup_cmd.start()

    def stop(self):
        """
        kosmos 'j.servers.openresty.stop()'
        :return:
        """
        self.startup_cmd.stop(waitstop=False, force=True)

    def is_running(self):
        """
        :return:
        """
        self.startup_cmd.is_running()

    def reload(self):
        """
        :return:
        """
        self.configure()
        cmd = "cd  %s;lapis build" % self._web_path
        j.sal.process.execute(cmd)
