import sys

from Jumpscale import j

JSConfigBase = j.baseclasses.object_config


class ThreeBotPackage(JSConfigBase):
    _SCHEMATEXT = """
        @url = jumpscale.threebot.package.1
        name** = "main"
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
        self._init_ = False

    def _init_before_action(self):
        if self._init_ == False:
            if self.giturl:
                self.path = j.clients.git.getContentPathFromURLorPath(self.giturl, branch=self.branch)

            # Parent root directory for packages needed to be in sys.path
            # in order to be able to import file properly inside packages
            packages_root = j.sal.fs.getParent(self.path)
            if not packages_root in sys.path:
                sys.path.append(packages_root)

            self._path_package = "%s/package.py" % (self.path)

            if not j.sal.fs.exists(self._path_package):
                raise j.exceptions.Input(
                    "cannot find package.py in the package directory", data={"path": self._path_package}
                )

            klass = j.tools.codeloader.load(obj_key="Package", path=self._path_package, reload=False)
            self._package = klass(package=self)
        self._init_ = True

    def prepare(self, *args):
        self._init_before_action()
        self._package.prepare(*args)

    def start(self):
        self._init_before_action()
        self._package.start()

    def stop(self):
        self._init_before_action()
        self._package.stop()

    def uninstall(self):
        self._init_before_action()
        self._package.uninstall()
