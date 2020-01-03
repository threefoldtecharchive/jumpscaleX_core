import sys

from Jumpscale import j
from Jumpscale.tools.threegit.ThreeGit import load_wiki

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
        name = ""
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
        lines = []
        model_prefix = f"{self.source.threebot}.{self.source.name}"

        for line in model.schema.text.splitlines():
            line = line.strip().lower()
            if line.startswith("@url"):
                continue
            lines.append(line)

        return "\n        ".join(lines)

    def load(self):

        if self._init_ is False:

            if not "bcdb" in j.threebot.__dict__:
                self._log_info("install in 3bot package:%s" % self)
                j.servers.threebot.require_threebotserver()
                pm = j.clients.gedis.get(name="packagemanager", port=8901, package_name="zerobot.packagemanager")
                self.package_manager_3bot = pm.actors.package_manager
                self.package_manager_3bot.package_add(path=self.path)
                # # means we are not in a threebot server
                return
            else:
                self.package_manager_3bot = None

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

                self.load_wiki(reset=True)

        self._init_ = True

    def load_wiki(self, reset=False):
        if self._wikis is None:
            self._wikis = j.baseclasses.dict()

        path = self.path + "/wiki"
        if j.sal.fs.exists(path):
            j.servers.myjobs.schedule(load_wiki, wiki_name=self.name, wiki_path=path, reset=reset)
            self._wikis[self.name] = path

    def actors_reload(self, reset=False):
        # def actors_crud_generate():
        #     for model_url in self.model_urls:
        #         found = True
        #         # Exclude bcdb meta data models
        #         model = self.bcdb.model_get(url=model_url)
        #         if model.schema.url.startswith("jumpscale.bcdb."):
        #             continue
        #         assert model_url.startswith(self.name)
        #
        #         shorturl = model_url[len(self.name) + 1 :].replace(".", "_")
        #         dest = self.path + "/actors/" + shorturl + "_model.py"
        #         # for now generate all the time TODO: change later
        #         if True or not j.sal.fs.exists(dest):
        #             j.tools.jinja2.file_render(
        #                 self._dirpath + "/templates/ThreebotModelCrudActorTemplate.py",
        #                 dest=dest,
        #                 model=model,
        #                 fields_schema=self._model_get_fields_schema(model),
        #                 shorturl=shorturl,
        #             )

        # def actors_crud_delete():
        #     for model_url in self.model_urls:
        #         model = self.bcdb.model_get(url=model_url)
        #         shorturl = model_url[len(self.name) + 1 :].replace(".", "_")
        #         dest = self.path + "/actors/" + shorturl + "_model.py"
        #         j.sal.fs.remove(dest)

        if self._actors is None or reset:
            self._actors = j.baseclasses.dict()
            package_toml = j.data.serializers.toml.load(f"{self.path}/package.toml")
            # if not ("disable_crud" in package_toml and package_toml["source"]["disable_crud"]):
            #     actors_crud_generate()  # will generate the actors for the model

            # actors_crud_delete()

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
        self.models  # always need to have the models
        if self._actors is None:
            self.load()
            self._actors = self.actors_reload()
        return self._actors

    @property
    def botsactor_names(self):
        res = []
        path = self.path + "actors"
        if j.sal.fs.exists(path):
            for fpath in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py", followSymlinks=True):
                res.append(j.sal.fs.getBaseName(fpath)[:-3])
        return res

    @property
    def models(self):
        if self._models is None:
            self.load()
            self._models = j.baseclasses.dict()
            path = self.path + "/models"
            if j.sal.fs.exists(path):
                model_urls = self.bcdb.models_add(path)
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
            self.load()
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
        self.load()
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
                if self.name:
                    name = self.name
                else:
                    name = "%s.%s" % (self.source.threebot, config.namespace)
                self._bcdb_ = j.data.bcdb.get_for_threebot(name=name, namespace=config.namespace, ttype=config.type)
            if len(self.bcdbs) == 0:
                self._bcdb_ = j.data.bcdb.system

        return self._bcdb_

    def bcdb_model_get(self, url):
        return self.bcdb.model_get(url=url)

    def _web_load(self, app_type="frontend"):
        for port in (443, 80):
            website = self.openresty.get_from_port(port)
            locations = website.locations.get(f"{self.name}_locations_{port}")
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
        #
        # if self.source.name == "system_bcdb":
        #     j.shell()

    def install(self):
        self.load()
        if self.package_manager_3bot:
            return
        else:
            if self.status != "config":  # make sure we load the config is not that state yet
                self.config_load()
            self._package_author.prepare()
            if self.status != "installed":
                self.status = "installed"
                self.save()

    def start(self):
        self.load()
        if self.package_manager_3bot:
            self.package_manager_3bot.package_start(name=self.name)
        else:
            if self.status != "installed":
                self.install()
            self._package_author.start()
            self.running = True
            self.save()

    def stop(self):
        self.load()
        if self.package_manager_3bot:
            self.package_manager_3bot.package_stop(name=self.name)
        else:
            self._package_author.stop()
            self.running = False
            self.save()

    def uninstall(self):
        self.load()
        self.stop()
        self.load()
        if self.package_manager_3bot:
            self.package_manager_3bot.package_delete(name=self.name)
        else:
            if self.status != "config":
                self.status = "config"
            self._package_author.uninstall()
            self.save()

    def disable(self):
        self.load()
        self.stop()
        if self.package_manager_3bot:
            self.package_manager_3bot.package_disable(name=self.name)
        else:
            if self.status != "disabled":
                self.status = "disabled"
            self.save()

    def enable(self):
        self.load()
        if self.package_manager_3bot:
            self.package_manager_3bot.package_enable(name=self.name)
        else:
            if self.status != "init":
                self.status = "init"
            self.install()

    def prepare(self):
        if self.package_manager_3bot:
            self.start()
            return
        self.load()
        self._package_author.prepare()
