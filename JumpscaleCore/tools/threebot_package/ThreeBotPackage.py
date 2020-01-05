import sys

from Jumpscale import j
from Jumpscale.tools.threegit.ThreeGit import load_wiki

from .ThreeBotPackageBase import ThreeBotPackageBase


class ThreeBotPackage(ThreeBotPackageBase):
    def _init_actor(self, **kwargs):
        self._changes = []
        self._actors = None
        self._chatflows = None

    @property
    def threebot_server(self):
        return j.threebot.servers.core

    @property
    def gedis_server(self):
        return j.servers.gedis.threebot
        # return j.threebot.servers.gedis

    @property
    def openresty(self):
        return j.threebot.servers.web

    def load(self):
        if self._init_ is False:
            packages_root = j.sal.fs.getParent(self.path)
            # if not packages_root in sys.path:
            #     sys.path.append(packages_root)
            path = self._changed("package.py")
            if path:
                klass, changed = j.tools.codeloader.load(obj_key="Package", path=path, reload=False)
                self._package_author = klass(package=self)
        self._init_ = True

    def _changed(self, path, die=True):
        if not path.startswith("/"):
            path = "%s/%s" % (self.path, path)
        if not j.sal.fs.exists(path):
            if die:
                raise j.exceptions.Input("could not find:%s" % path)
            else:
                return None
        if j.sal.fs.isDir(path):
            md5 = j.sal.fs.getFolderMD5sum(path, ignore_empty_files=True)
        elif j.sal.fs.isFile(path):
            md5 = j.sal.fs.md5sum(path)
        else:
            raise j.exceptions.Input("could not check change only file or dir supported:%s" % path)
        if md5 not in self._changes:
            self._changes.append(md5)
            return path
        return None

    def reload(self, reset=False):

        self.load()

        # Parent root directory for packages needed to be in sys.path
        # in order to be able to import file properly inside packages

        path = self._changed("html", die=False)
        if path:
            self._web_load("html")

        path = self._changed("frontend", die=False)
        if path:
            self._web_load("frontend")

        # if j.sal.fs.exists(self.path + "/bottle"):
        #     # load webserver
        #     j.shell()

        self.actors_load()
        self.chatflows_load()
        self.wiki_load(reset=reset)

        if hasattr(j.threebot, "servers"):
            self.openresty.reload()

    def wiki_load(self, reset=False):
        self.load()

        if self._wikis is None:
            self._wikis = j.baseclasses.dict()

        path = self._changed("wiki", die=False)
        if path:
            j.servers.myjobs.schedule(load_wiki, wiki_name=self.name, wiki_path=path, reset=reset)
            self._wikis[self.name] = path

    def actors_load(self):

        self.load()
        self.models

        path = self._changed("actors", die=False)
        if path:
            if self._actors is None:
                self._actors = j.baseclasses.dict()
            for fpath in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py", followSymlinks=True):
                # TODO: why do we use this try/except construct?
                try:
                    cl, changed = j.tools.codeloader.load(obj_key=None, path=fpath, reload=False, md5=None)
                except Exception as e:
                    errormsg = "****ERROR HAPPENED IN LOADING ACTOR: %s\n%s" % (fpath, e)
                    self._log_error(errormsg)
                    print(errormsg)
                    raise e
                if changed:
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

    @property
    def actors(self):
        self.models  # always need to have the models
        if self._actors is None:
            self.load()
            self.reload()
            # self.actors_load()
        return self._actors

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
    def wiki_names(self):
        return [item for item in self.wikis.keys()]

    @property
    def models(self):
        if self._models is None:
            self.load()
            self._models = j.baseclasses.dict()
            path = self._changed("models", die=False)
            if path:
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
    def chat_names(self):
        if self._chatflows is None:
            self.load()
            self.chatflows_load()
        return self._chatflows

    def chatflows_load(self):
        self._chatflows = j.baseclasses.dict()
        self.load()
        path = self._changed("chatflows", die=False)
        if path:
            self._chatflows = self.gedis_server.chatbot.chatflows_load(path)

    @property
    def wikis(self):
        # lazy-loading of wikis would take time, user will wait for too long
        # and need to refresh to see loaded wikis
        self.wiki_load()
        return self._wikis

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
        if self.status != "config":  # make sure we load the config is not that state yet
            self.config_load()
        self._package_author.prepare()
        if self.status != "installed":
            self.status = "installed"
            self.save()

    def start(self):
        self.load()
        if self.status != "installed":
            self.install()
        self._package_author.start()
        self.running = True
        self.save()

    def stop(self):
        self.load()
        self._package_author.stop()
        self.running = False
        self.save()

    def uninstall(self):
        self.load()
        self.stop()
        self.load()
        if self.status != "config":
            self.status = "config"
        self._package_author.uninstall()
        self.save()

    def disable(self):
        self.load()
        self.stop()
        if self.status != "disabled":
            self.status = "disabled"
        self.save()

    def enable(self):
        self.load()
        if self.status != "init":
            self.status = "init"
        self.install()

    def prepare(self):
        self.load()
        self._package_author.prepare()

    def _model_get_fields_schema(self, model):
        lines = []
        model_prefix = f"{self.source.threebot}.{self.source.name}"

        for line in model.schema.text.splitlines():
            line = line.strip().lower()
            if line.startswith("@url"):
                continue
            lines.append(line)

        return "\n        ".join(lines)
