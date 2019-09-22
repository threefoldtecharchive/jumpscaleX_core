from .Website import Websites
from Jumpscale import j

JSBASE = j.baseclasses.object

# WIKI_CONFIG_TEMPLATE = "templates/WIKI_CONF_TEMPLATE.conf"
# WEBSITE_CONFIG_TEMPLATE = "templates/WEBSITE_CONF_TEMPLATE.conf"
# WEBSITE_STATIC_CONFIG_TEMPLATE = "templates/WEBSITE_STATIC_CONF_TEMPLATE.conf"
# OPEN_PUBLISH_REPO = "https://github.com/threefoldtech/OpenPublish"


class OpenRestyServer(j.baseclasses.factory_data):
    """
    Factory for openresty
    """

    _CHILDCLASSES = [Websites]
    _SCHEMATEXT = """
           @url =  jumpscale.openresty.server.1
           name** = "default" (S)
           host = "127.0.0.1" (S)
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
        self.path_web_default = "/sandbox/var/web/default"
        self.path_web = "/sandbox/var/web/%s" % self.name
        self.path_cfg_dir = "/sandbox/cfg/nginx/%s" % self.name
        self.path_cfg = "%s/nginx.conf" % self.path_cfg_dir
        j.sal.fs.createDir(self.path_web)
        j.sal.fs.createDir(self.path_cfg_dir)

        self.executor = "tmux"  # only tmux for now

        self.install()

        self.configure()

    def configure(self):
        self.install()
        configtext = j.tools.jinja2.file_render(path=f"{self._dirpath}/templates/nginx.conf", obj=self)
        j.sal.fs.writeFile(self.path_cfg, configtext)

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
            j.sal.fs.copyDirTree("%s/web_resources/" % self._dirpath, self.path_cfg_dir)

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
            # j.sal.fs.copyFile(
            #     "%s/web_resources/lualib/websocket.lua" % self._dirpath, "/sandbox/openresty/lualib/websocket.lua"
            # )
            self.status = "installed"

            self.save()

    def _letsencrypt_configure(self):
        """
        add location required by let's encrypt to any website listening on port 80
        """

        ssl = False
        listening_80 = None
        for website in self.websites.find():
            if website.ssl:
                ssl = True
            if website.port == 80:
                listening_80 = website

        if not ssl:
            return

        if not listening_80:
            listening_80 = self.websites.new("listening_80")
            listening_80.port = 80
            listening_80.ssl = False

        listening_80.configure()
        location_dir = f"{listening_80.path_cfg_dir}/{listening_80.name}_locations"
        j.sal.fs.createDir(location_dir)
        j.sal.fs.copyFile(
            f"{self._dirpath}/templates/letsencrypt_challenge_location.conf", f"{location_dir}/letsencrypt.conf"
        )

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
                path=self.path_cfg_dir,
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
        self._letsencrypt_configure()
        # compile all 1 time to lua, can do this at each start
        j.sal.process.execute("cd %s;moonc ." % self._web_path)
        if reset:
            self.startup_cmd.stop(force=True)
        if self.startup_cmd.is_running():
            self.stop()
            self.reload()

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
        cmd = "cd  %s;lapis build" % self.path_cfg_dir
        j.sal.process.execute(cmd)
