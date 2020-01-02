import sys

from Jumpscale import j
from Jumpscale.tools.threegit.ThreeGit import load_wiki


class ThreeBotPackageBase(j.baseclasses.object_config):
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

        self._files_loaded = j.baseclasses.dict()

    @property
    def actor_names(self):
        res = []
        path = self.path + "actors"
        if j.sal.fs.exists(path):
            for fpath in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py", followSymlinks=True):
                res.append(j.sal.fs.getBaseName(fpath)[:-3])
        return res

    @property
    def model_urls(self):
        return [item.schema.url for item in self.models.values()]

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
    def models(self):
        if self._models is None:
            self.load()
            self._models = j.baseclasses.dict()
            # need to use bcdbmodel client, prob need actor method to know the models
            j.shell()
        return self._models

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
