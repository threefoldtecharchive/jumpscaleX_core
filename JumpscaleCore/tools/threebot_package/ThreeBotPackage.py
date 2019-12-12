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

        # load current models
        self.models

    @property
    def fullname(self):
        """get a dot separated fully qualified name of the package"""
        return f"{self.source.threebot}.{self.source.name}"

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
        lines = []

        for line in model.schema.text.splitlines():
            line = line.strip().lower()
            if line.startswith("@url"):
                continue

            try:
                model_url = line[line.index("!") + 1 :].split("#")[0]
                for prefix in ["jumpscale", "zerobot", "tfgrid", "threefold"]:
                    if model_url.startswith(prefix):
                        break
                else:
                    old_model_url = model_url
                    model_url = f"{self.fullname}.{model_url}"
                    line = line.replace(old_model_url, model_url)
            except ValueError:
                # ! is not in line
                pass

            lines.append(line)

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

            def load_wiki(wiki_name=None, wiki_path=None):
                """we cannot use name parameter with myjobs.schedule, it has a name parameter itself"""
                wiki = j.tools.markdowndocs.load(name=wiki_name, path=wiki_path, pull=False)
                wiki.write()

            if self._wikis is None:
                self._wikis = j.baseclasses.dict()

            path = self.path + "/wiki"
            if j.sal.fs.exists(path):
                j.servers.myjobs.schedule(load_wiki, wiki_name=self.name, wiki_path=path)
                self._wikis[self.name] = path

        self._init_ = True

    def actors_reload(self, reset=False):
        def actors_crud_generate():
            for model_url in self.model_urls:
                found = True
                # Exclude bcdb meta data models
                model = self.bcdb.model_get(url=model_url, package=self)
                if model.schema.url.startswith("jumpscale.bcdb."):
                    continue
                assert model_url.startswith(self.fullname)

                shorturl = model_url[len(self.fullname) + 1 :].replace(".", "_")
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

        if self._actors is None or reset:
            self._actors = j.baseclasses.dict()
            package_toml = j.data.serializers.toml.load(f"{self.path}/package.toml")
            if not ("disable_crud" in package_toml and package_toml["source"]["disable_crud"]):
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
                    # print(f"adding actor {name} {fpath} {self.name}")
                    self.gedis_server.actor_add(name=name, path=fpath, package=self)
        return self._actors

    @property
    def actors(self):
        if self._actors is None:
            self._actors = self.actors_reload()
        return self._actors

    @property
    def actor_names(self):
        return list(self.actors.keys())

    @property
    def models(self):
        if self._models is None:
            self._models = j.baseclasses.dict()
            path = self.path + "/models"
            if j.sal.fs.exists(path):
                model_urls = self.bcdb.models_add(path, package=self)
                for model_url in model_urls:
                    m = self.bcdb.model_get(url=model_url, package=self)
                    if model_url.startswith(self.fullname):
                        model_url2 = model_url[len(self.fullname) + 1 :]
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
                self._chatflows = self.gedis_server.chatbot.chatflows_load(path)
        return self._chatflows

    @property
    def chat_names(self):
        return [item for item in self.chatflows]

    @property
    def wikis(self):
        # lazy-loading of wikis would take time, user will wait for too long
        # and need to refresh to see loaded wikis
        return self._wikis

    @property
    def wiki_names(self):
        return [item for item in self.wikis.keys()]

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

    def bcdb_model_get(self, url):
        return self.bcdb.model_get(url=url, package=self)

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
            raise j.exceptions.Input(f"cannot find config file in path {tomlfile} for package {self.name}")
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
