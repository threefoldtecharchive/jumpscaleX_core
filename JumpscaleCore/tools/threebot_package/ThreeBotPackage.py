from Jumpscale import j

JSConfigBase = j.baseclasses.object_config


class ThreeBotPackage(JSConfigBase):
    _SCHEMATEXT = """
        @url = jumpscale.threebot.package.1
        name* = "main"
        giturl = "" (S)  #if empty then local
        path = ""
        threebot_server_name = "default"
        branch = ""
        """

    @property
    def threebot_server(self):
        return j.servers.threebot.get(name=self.threebot_server_name)

    @property
    def gedis_server(self):
        return self.threebot_server.gedis_server

    @property
    def openresty(self):
        return self.threebot_server.openresty_server

    def _init(self, **kwargs):
        if self.giturl:
            self.path = j.clients.git.getContentPathFromURLorPath(self.giturl, branch=self.branch)

        self._path_package = "%s/package.py" % (self.path)

        if not j.sal.fs.exists(self._path_package):
            raise j.exceptions.Input(
                "cannot find package.py in the package directory", data={"path": self._path_package}
            )

        klass = j.tools.codeloader.load(obj_key="Package", path=self._path_package, reload=False)
        self._package = klass(package=self)

        self.prepare = self._package.prepare
        self.start = self._package.start
        self.stop = self._package.stop
        self.uninstall = self._package.uninstall
