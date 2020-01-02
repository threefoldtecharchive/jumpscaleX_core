import sys

from Jumpscale import j
from Jumpscale.tools.threegit.ThreeGit import load_wiki

from .ThreeBotPackageBase import ThreeBotPackageBase


class ThreeBotPackageClient(ThreeBotPackageBase):
    def load(self):

        if self._init_ is False:

            self._log_info("install in 3bot package:%s" % self)
            j.servers.threebot.require_threebotserver()
            pm = j.clients.gedis.get(name="packagemanager", port=8901, package_name="zerobot.packagemanager")
            self.package_manager_3bot = pm.actors.package_manager
            self.package_manager_3bot.package_add(path=self.path)
            # # means we are not in a threebot server
            return

        self._init_ = True

    def wiki_load(self, reset=False):
        return self.package_manager_3bot.wiki_load(reset=reset)

    def reload(self, reset=False):
        return self.package_manager_3bot.reload(reset=reset)

    @property
    def actors(self):
        # create client connections to actors
        j.shell()

    @property
    def actor_names(self):
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
        # print(f"tomfile: {tomlfile}")
        if not j.sal.fs.exists(tomlfile):
            raise j.exceptions.Input(f"cannot find config file in path {tomlfile} for package {self.name}")
        config = j.data.serializers.toml.loads(j.sal.fs.readFile(tomlfile))
        self._data._data_update(config)

        if self.status == "init":  # should only move the config status if in init
            self.status = "config"
            self.save()

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
        self.package_manager_3bot.package_start(name=self.name)

    def stop(self):
        self.load()
        self.package_manager_3bot.package_stop(name=self.name)

    def uninstall(self):
        self.load()
        self.stop()
        self.load()
        self.package_manager_3bot.package_delete(name=self.name)

    def disable(self):
        self.load()
        self.stop()
        self.package_manager_3bot.package_disable(name=self.name)

    def enable(self):
        self.load()
        self.package_manager_3bot.package_enable(name=self.name)

    def prepare(self):
        self.start()
