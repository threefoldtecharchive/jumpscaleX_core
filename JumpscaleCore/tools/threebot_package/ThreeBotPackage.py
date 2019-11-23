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

    # @property
    # def threebot_server(self):
    #     return j.servers.threebot.get(name=self.threebot_server_name)
    #
    # @property
    # def gedis_server(self):
    #     return self.threebot_server.gedis_server
    #
    # @property
    # def openresty(self):
    #     return self.threebot_server.openresty_server

    def _init(self, **kwargs):
        self._init_ = False

    def _init_before_action(self):

        if not "bcdb" in j.threebot.__dict__:
            # means we are not in a threebot server, should not allow the following to happen
            raise j.exceptions.Base("cannot use threebot package data model from process out of threebot")

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

            def load_wiki(wiki_name=None, wiki_path=None):
                """we cannot use name parameter with myjobs.schedule, it has a name parameter itself"""
                wiki = j.tools.markdowndocs.load(name=wiki_name, path=wiki_path, pull=False)
                wiki.write()

            path = self.path + "/wiki"
            if j.sal.fs.exists(path):
                name = self.name
                j.servers.myjobs.schedule(load_wiki, wiki_name=name, wiki_path=path)

            self._create_locations()

        self._init_ = True

    def _check_app_type(self):
        html_location = j.sal.fs.joinPaths(self.path, "html")
        frontend_location = j.sal.fs.joinPaths(self.path, "frontend")
        if j.sal.fs.exists(frontend_location):
            return "frontend"
        elif j.sal.fs.exists(html_location):
            return "html"

    def _create_locations(self):
        if not self.path:
            return
        app_type = self._check_app_type()
        if app_type:
            for port in (443, 80):
                website = self.openresty.get_from_port(port)

                locations = website.locations.get(f"{self.name}_locations")
                if app_type == "frontend":
                    website_location = locations.locations_spa.new()
                elif app_type == "html":
                    website_location = locations.locations_static.new()

                website_location.name = self.name
                website_location.path_url = f"/{self.name}"
                website_location.use_jumpscale_weblibs = False
                fullpath = j.sal.fs.joinPaths(self.path, f"{app_type}/")
                website_location.path_location = fullpath

                locations.configure()
                website.configure()

    @property
    def bcdb(self):
        return self._package_author.bcdb

    def prepare(self):
        self._init_before_action()
        self._package_author.prepare()

    def start(self):
        self._init_before_action()
        self._package_author.start()
        self.status = "running"
        self.save()

    def stop(self):
        self._init_before_action()
        self._package_author.stop()
        self.status = "halted"
        self.save()

    def uninstall(self):
        self._init_before_action()
        self._package_author.uninstall()

    def disable(self):
        self.status = "disabled"
        self.save()

    def enable(self):
        self.status = "installed"
        self.save()
