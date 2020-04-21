import sys

from Jumpscale import j
from .ThreeBotPackageBase import ThreeBotPackageBase


class ThreeBotPackageClient(ThreeBotPackageBase):
    def load(self):
        if self._init_ is False:
            self._log_info("install in 3bot package:%s" % self)
            j.servers.threebot.threebotserver_require()
            pm = j.clients.gedis.get(name="packagemanager", port=8901, package_name="zerobot.admin")
            self.package_manager_3bot = pm.actors.package_manager
            self.package_manager_3bot.package_add(path=self.path)
            self._gedisclient = None
        self._init_ = True

    @property
    def gedisclient(self):
        self.load()
        if not self._gedisclient:
            self._gedisclient = j.clients.gedis.get(name=self.name, port=8901, package_name=self.name)
        return self._gedisclient

    @property
    def actors(self):
        return self.gedisclient.actors

    @property
    def actor_names(self):
        res = []
        path = self.path + "actors"
        if j.sal.fs.exists(path):
            for fpath in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py", followSymlinks=True):
                res.append(j.sal.fs.getBaseName(fpath)[:-3])
        return res

    # @property
    # def models(self):
    #     if self._models is None:
    #         self.load()
    #         self._models = j.baseclasses.dict()
    #         path = self.path + "/models"
    #         if j.sal.fs.exists(path):
    #             model_urls = self.bcdb.models_add(path)
    #             for model_url in model_urls:
    #                 m = self.bcdb.model_get(url=model_url)
    #                 if model_url.startswith(self.name):
    #                     model_url2 = model_url[len(self.name) + 1 :]
    #                 else:
    #                     model_url2 = model_url
    #                 model_url3 = model_url2.replace(".", "__")
    #                 self._models[model_url3] = m
    #     return self._models
    #
    # @property
    # def model_urls(self):
    #     return [item.schema.url for item in self.models.values()]

    # @property
    # def chatflows(self):
    #     if self._chatflows is None:
    #         self.load()
    #         self._chatflows = j.baseclasses.dict()
    #         path = self.path + "/chatflows"
    #         if j.sal.fs.exists(path):
    #             self._chatflows = self.gedis_server.chatbot.chatflows_load(path)
    #     return self._chatflows

    # @property
    # def chat_names(self):
    #     return [item for item in self.chatflows]

    # @property
    # def wikis(self):
    #     # lazy-loading of wikis would take time, user will wait for too long
    #     # and need to refresh to see loaded wikis
    #     self.load()
    #     return self._wikis
    #
    # @property
    # def wiki_names(self):
    #     return [item for item in self.wikis.keys()]

    @property
    def models(self):
        if self._models is None:
            self.load()
            self._models = j.baseclasses.dict()
            # need to use bcdbmodel client, prob need actor method to know the models
            r = self.package_manager_3bot.model_urls_list(package_name=self.name).packages[0]
            for url in r.urls:
                self._models[url] = j.clients.bcdbmodel.get(name=r.bcdb_name, url=url)
        return self._models

    def bcdb_model_get(self, url):
        return self.models[url]

    # def _web_load(self, app_type="frontend"):
    #     for port in (443, 80):
    #         website = self.openresty.get_from_port(port)
    #         locations = website.locations.get(f"{self.name}_locations_{port}")
    #         if app_type == "frontend":
    #             website_location = locations.locations_spa.new()
    #         elif app_type == "html":
    #             website_location = locations.locations_static.new()
    #
    #         website_location.name = self.name
    #         website_location.path_url = f"/{self.source.threebot}/{self.source.name}"
    #         website_location.use_jumpscale_weblibs = False
    #         fullpath = j.sal.fs.joinPaths(self.path, f"{app_type}/")
    #         website_location.path_location = fullpath
    #
    #         locations.configure()
    #         website.configure()

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
        return

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

    def reload(self, reset=False):
        self.load()
        return self.package_manager_3bot.package_reload(package_name=self.name, reset=reset)
