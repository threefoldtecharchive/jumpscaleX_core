import sys

from Jumpscale import j

JSConfigBase = j.baseclasses.object_config


class ThreeBotPackage(JSConfigBase):

    _SCHEMATEXT = """
        @url = jumpscale.threebot.package.1
        name** = "main"
        giturl = "" (S)  #if empty then local
        branch = "" (S)
        path = ""
        status = "init,config,installed,disabled,error" (E)
        source = (O) !jumpscale.threebot.package.source.1
        actor = (O) !jumpscale.threebot.package.actor.1
        bcdbs = (LO) !jumpscale.threebot.package.bcdb.1


        @url = jumpscale.threebot.package.source.1
        name = ""
        threebot = ""
        description = ""
        version = "" (S)

        @url = jumpscale.threebot.package.actor.1
        namespace = ""

        @url = jumpscale.threebot.package.bcdb.1
        namespace = ""
        type = "zdb,sqlite,redis" (E)
        instance = "default"

        """

    def _init(self, **kwargs):
        self._init_ = False
        self._bcdb_ = None  # cannot use self._bcdb already used
        if self.status == "init":
            self.config_load()
        self.running = False
        if self.giturl and not self.branch:
            self.branch = "master"

        # should not be part of our DB object
        self._actors = None
        self._models = None
        self._wikis = None
        self._chatflows = None

        # self.chat_names = []
        # self.wiki_names = []
        # self.model_urls = []

    @property
    def threebot_server(self):
        return j.threebot.servers.core

    @property
    def gedis_server(self):
        return j.threebot.servers.gedis

    @property
    def openresty(self):
        return j.threebot.servers.web

    def _model_get_fields_schema(self, model):
        lines = model.schema.text.splitlines()
        if lines[0].strip().startswith("@url"):
            lines.pop(0)
        return "\n        ".join(lines)

    def load(self):
        if not "bcdb" in j.threebot.__dict__:
            # means we are not in a threebot server, should not allow the following to happen
            raise j.exceptions.Base("cannot use threebot package data model from process out of threebot")

        if self._init_ == False:

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

            if j.sal.fs.exists(self.path + "/html"):
                self._web_load("html")
            elif j.sal.fs.exists(self.path + "/frontend"):
                self._web_load("frontend")

            # if j.sal.fs.exists(self.path + "/bottle"):
            #     # load webserver
            #     j.shell()

        self._init_ = True

    @property
    def actors(self):
        def actors_crud_generate():
            for model_url in self.model_urls:
                found = True
                # Exclude bcdb meta data models
                model = self.bcdb.model_get(url=model_url, package=self)
                if model.schema.url.startswith("jumpscale.bcdb."):
                    continue
                assert model_url.startswith(self.name)

                shorturl = model_url[len(self.name) + 1 :].replace(".", "_")
                dest = self.path + "/actors/" + shorturl + "_model.py"
                # for now generate all the time TODO: change later
                if True or not j.sal.fs.exists(dest):
                    j.tools.jinja2.file_render(
                        self._dirpath + "/templates/ThreebotModelCrudActorTemplate.py",
                        dest=dest,
                        model=model,
                        fields_schema=self._model_get_fields_schema(model),
                        shorturl=shorturl,
                    )

        if self._actors is None:
            self._actors = j.baseclasses.dict()
            actors_crud_generate()  # will generate the actors for the model
            path = self.path + "/actors"
            if j.sal.fs.exists(path):

                for fpath in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py", followSymlinks=True):
                    try:
                        cl = j.tools.codeloader.load(obj_key=None, path=fpath, reload=False, md5=None)
                    except Exception as e:
                        errormsg = "****ERROR HAPPENED IN LOADING ACTOR: %s\n%s" % (fpath, e)
                        self._log_error(errormsg)
                        print(errormsg)
                        raise e
                    name = j.tools.codeloader._basename(fpath).lower()
                    try:
                        self._actors[name] = cl(package=self)
                    except Exception as e:
                        errormsg = "****ERROR HAPPENED IN LOADING ACTOR: %s\n%s" % (fpath, e)
                        self._log_error(errormsg)
                        print(errormsg)
                        raise e

        return self._actors

    def gedis_activate(self, server):
        path = self.path + "/actors"
        if j.sal.fs.exists(path):
            server.actors_add(path, package=self)

    @property
    def actor_names(self):
        return [item.name for item in self.actors.values()]

    @property
    def models(self):
        if self._models is None:
            self._models = j.baseclasses.dict()
            path = self.path + "/models"
            if j.sal.fs.exists(path):
                model_urls = self.bcdb.models_add(path, package=self)
                for model_url in model_urls:
                    m = self.bcdb.model_get(url=model_url)
                    if model_url.startswith(self.name):
                        model_url2 = model_url[len(self.name) + 1 :]
                    else:
                        model_url2 = model_url
                    model_url3 = model_url2.replace(".", "__")
                    self._models[model_url3] = m
        return self._models

    @property
    def model_urls(self):
        return [item.schema.url for item in self.models.values()]

    @property
    def chatflows(self):
        if self._chatflows is None:
            self._chatflows = j.baseclasses.dict()
            path = self.path + "/chatflows"
            if j.sal.fs.exists(path):
                chatflows = self.gedis_server.chatbot.chatflows_load(path)
                j.shell()
                w

        return self._chatflows

    @property
    def chat_names(self):
        return [item.name for item in self.chatflows]

    @property
    def wikis(self):
        def load_wiki(wiki_name=None, wiki_path=None):
            """we cannot use name parameter with myjobs.schedule, it has a name parameter itself"""
            wiki = j.tools.markdowndocs.load(name=wiki_name, path=wiki_path, pull=False)
            wiki.write()

        if self._wikis is None:
            self._wikis = j.baseclasses.dict()
            path = self.path + "/wiki"
            if j.sal.fs.exists(path):
                j.servers.myjobs.schedule(load_wiki, wiki_name=self.name, wiki_path=path)
                j.shell()
                w

        return self._wikis

    @property
    def wiki_names(self):
        return [item for item in self.wikis]

    @property
    def bcdb(self):
        if not self._bcdb_:
            ##GET THE BCDB, ONLY 1 support for now
            if len(self.bcdbs) == 1:
                config = self.bcdbs[0]
                assert config.instance == "default"  # for now we don't support anything else
                self._bcdb_ = j.data.bcdb.get_for_threebot(
                    namespace=config.namespace, ttype=config.type, instance=config.instance
                )
            if len(self.bcdbs) == 0:
                self._bcdb_ = j.data.bcdb.system

        return self._bcdb_

    def _web_load(self, app_type="frontend"):
        for port in (443, 80):
            website = self.openresty.get_from_port(port)
            locations = website.locations.get(f"{self.name}_locations")
            if app_type == "frontend":
                website_location = locations.locations_spa.new()
            elif app_type == "html":
                website_location = locations.locations_static.new()

            website_location.name = self.name
            website_location.path_url = f"/{self.source.threebot}/{self.source.name}"
            website_location.use_jumpscale_weblibs = False
            fullpath = j.sal.fs.joinPaths(self.path, f"{app_type}/")
            website_location.path_location = fullpath

            locations.configure()
            website.configure()

    def config_load(self):
        self._log_info("load package.toml config", data=self)
        if self.giturl:
            self.path = j.clients.git.getContentPathFromURLorPath(self.giturl, branch=self.branch)
        tomlfile = f"{self.path}/package.toml"
        if not j.sal.fs.exists(tomlfile):
            raise j.exceptions.NotFound(f"cannot find package.toml in path")
        if not j.sal.fs.exists(tomlfile):
            raise j.exceptions.Input("cannot find config file on:%s" % tomlfile)
        config = j.data.serializers.toml.loads(j.sal.fs.readFile(tomlfile))
        self._data._data_update(config)

        if self.status == "init":  # should only move the config status if in init
            self.status = "config"
            self.save()

    def install(self):
        self.load()
        if self.status != "config":  # make sure we load the config is not that state yet
            self.config_load()
        self._package_author.prepare()
        if self.status != "installed":
            self.status = "installed"
            self.save()

    def start(self):
        if self.status != "installed":
            self.install()
        self.load()
        # should be merged into load method later on
        self._package_author.start()
        self.running = True
        self.save()

    def stop(self):
        self.load()
        self._package_author.stop()
        self.running = False
        self.save()

    def uninstall(self):
        self.stop()
        if self.status != "config":
            self.status = "config"
        self._package_author.uninstall()
        self.save()

    def disable(self):
        self.stop()
        if self.status != "disabled":
            self.status = "disabled"
        self.save()

    def enable(self):
        if self.status != "init":
            self.status = "init"
        self.install()

    def prepare(self):
        self._package_author.prepare()
