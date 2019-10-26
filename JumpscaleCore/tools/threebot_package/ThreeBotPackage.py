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
        status = "init,installed,running,halted,disabled,error" (E)
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
            self._package_author = klass(package=self)

            path = self.path + "/models"
            if j.sal.fs.exists(path):
                self.bcdb.models_add(path)

            path = self.path + "/actors"
            if j.sal.fs.exists(path):
                self.gedis_server.actors_add(path, namespace=self._package_author.actors_namespace)

            path = self.path + "/chatflows"
            if j.sal.fs.exists(path):
                self.gedis_server.chatbot.chatflows_load(path)

            # TODO: load macros's (THABET TO PLAN)

            chatflows_path = self.path + "/chatflows"
            if j.sal.fs.exists(chatflows_path):
                self.gedis_server.chatbot.chatflows_load(chatflows_path)

            def load_wiki(path=None, name=None):
                wiki = j.tools.markdowndocs.load(path=path, name=name, pull=False)
                wiki.write()

            path = self.path + "/wiki"
            if j.sal.fs.exists(path):
                name = self.name
                j.servers.myjobs.schedule(load_wiki, name=name, path=path)


        self._init_ = True

    @property
    def bcdb(self):
        return self._package_author.bcdb

    def prepare(self):
        self._init_before_action()
        self._package_author.prepare()

    def start(self):
        self._init_before_action()
        self._package_author.start()

    def stop(self):
        self._init_before_action()
        self._package_author.stop()

    def uninstall(self):
        self._init_before_action()
        self._package_author.uninstall()

    def disable(self):
        self.status = "disabled"
        self.save()
