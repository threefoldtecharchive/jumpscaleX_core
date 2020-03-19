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
        self._web_path = j.core.tools.text_replace("{DIR_BASE}/var/web/%s" % self.name)
        self.path_web_default = j.core.tools.text_replace("{DIR_BASE}/var/web/default")
        self.path_web = j.core.tools.text_replace("{DIR_BASE}/var/web/%s" % self.name)
        self.path_cfg_dir = j.core.tools.text_replace("{DIR_BASE}/cfg/nginx/%s" % self.name)
        self.path_cfg = "%s/nginx.conf" % self.path_cfg_dir
        self.logs_dir = j.core.tools.text_replace("{DIR_BASE}/var/logs/openresty/%s" % self.name)
        j.sal.fs.createDir(self.path_web)
        j.sal.fs.createDir(self.path_cfg_dir)
        j.sal.fs.createDir(self.logs_dir)
        # clean old websites config
        self.cleanup()
        self.executor = "tmux"  # only tmux for now

        self.install()

        self.configure()

    def configure(self):
        self.install()
        configtext = j.tools.jinja2.file_render(
            path=f"{self._dirpath}/templates/nginx.conf", obj=self, logs_dir=self.logs_dir, write=False
        )
        j.sal.fs.writeFile(self.path_cfg, configtext)

    def get_from_port(self, port, domain=None, ssl=None):
        """
        will try to get a website listening on port, if it doesn't exist it will create one
        :param port:
        :return: website

        :param port: port to search for
        :type port: int
        :param domain: domain, defaults to None
        :type domain: str, optional
        :param ssl: set ssl, defaults to None
        :type ssl: bool, optional
        :return: a new or an old website instance with the same port
        :rtype: Website
        """

        for website in self.websites.find():
            if website.port == port:
                return website

        ws = self.websites.get(f"website_{port}", port=port, domain=domain)
        if ssl is None:
            ws.ssl = port == 443
        else:
            ws.ssl = ssl

        return ws

    def install(self, reset=False):
        """
        kosmos 'j.servers.openresty.default.install(reset=True)'
        :param reset:
        :return:
        """
        if reset or self.status not in ["ok", "installed"]:

            # get weblib
            url = "https://github.com/threefoldtech/jumpscaleX_weblibs"
            weblibs_path = j.clients.git.getContentPathFromURLorPath(url, pull=False, branch="master")

            # copy the templates to the right location
            j.sal.fs.copyDirTree("%s/web_resources/" % self._dirpath, self.path_cfg_dir)

            j.sal.fs.symlink(
                "%s/static" % weblibs_path, "{}/static/weblibs".format(self._web_path), overwriteTarget=True
            )
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
            cmd = "lapis server"
            self._cmd = j.servers.startupcmd.get(
                name="lapis",
                cmd_start=cmd,
                path=self.path_cfg_dir,
                process_name="openresty",
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
        self.cleanup()
        self.install(reset=reset)
        self.configure()
        self._letsencrypt_configure()

        # compile all 1 time to lua, can do this at each start
        # j.sal.process.execute("cd %s;moonc ." % self._web_path)
        # NO LONGER NEEDED BECAUSE WE DON"T USE THE MOONSCRIPT ANY MORE
        self._log_info("Starting Lapis Server")
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

    def cleanup(self):
        j.sal.fs.remove("%s/servers" % self.path_cfg_dir)
