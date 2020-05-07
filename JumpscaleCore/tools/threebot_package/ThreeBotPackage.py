import sys
from Jumpscale import j

from .ThreeBotPackageBase import ThreeBotPackageBase


def generate_path_md5(path):
    if j.sal.fs.isDir(path):
        md5 = j.sal.fs.getFolderMD5sum(path, ignore_empty_files=True)
    elif j.sal.fs.isFile(path):
        md5 = j.sal.fs.md5sum(path)
    else:
        raise j.exceptions.Input("could not check change only file or dir supported:%s" % path)
    return md5


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

    @property
    def openresty(self):
        return j.threebot.servers.web

    def load(self):
        """
        SHOULD ONLY LOAD THE PACKAGE FILE, NOTHING MORE
        :return:
        """
        if not self._init_:
            path = j.sal.fs.joinPaths(self.path, "package.py")
            klass, _ = j.tools.codeloader.load(obj_key="Package", path=path, reload=False)
            self._package_author = klass(package=self)
        self._init_ = True

    def _changed(self, path, die=True, reset=False):
        if not path.startswith("/"):
            path = j.sal.fs.joinPaths(self.path, path)
        if not j.sal.fs.exists(path):
            if die:
                raise j.exceptions.Input("could not find:%s" % path)
            else:
                return None
        md5 = generate_path_md5(path)
        if md5 not in self._changes or reset:
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

        wiki_path = j.sal.fs.joinPaths(self.path, "wiki")
        if not j.sal.fs.exists(wiki_path):
            return

        try:
            j.tools.mdbook.load(self.name, wiki_path)
        except j.exceptions.Base as e:
            self._log_error(f"error loading wiki of {self.name}", exception=e)
            return

        self._wikis[self.name] = wiki_path

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
                        self._actors = None
                        raise e
                        # print(f"adding actor {name} {fpath} {self.name}")
                    self.gedis_server.actor_add(name=name, path=fpath, package=self)

    def actors_remove(self):
        self.load()
        # Get the full path for actors in the package
        path = "actors"
        if not path.startswith("/"):
            path = j.sal.fs.joinPaths(self.path, path)
        if not j.sal.fs.exists(path):
            return

        # remove the actors
        if path:
            if self._actors is None:
                self._actors = j.baseclasses.dict()
            for fpath in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py", followSymlinks=True):
                # unload the hashed actors
                try:
                    j.tools.codeloader.unload(obj_key=None, path=fpath, reload=False, md5=None)
                except Exception as e:
                    errormsg = "****ERROR HAPPENED IN unloading ACTOR: %s\n%s" % (fpath, e)
                    self._log_error(errormsg)
                    print(errormsg)
                    raise e

                name = j.tools.codeloader._basename(fpath).lower()
                self.gedis_server.actors_remove(name=name, package=self)

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
                if not config.name:
                    raise j.exceptions.Input(
                        f"could not find name for bcdb in config of package, {self.name}, found {config.name}"
                    )
                self._bcdb_ = j.data.bcdb.get_for_threebot(
                    name=config.name, namespace=config.namespace, ttype=config.type
                )
            elif len(self.bcdbs) == 0:
                self._bcdb_ = j.data.bcdb.system
            else:
                raise j.exceptions.Input("only support 1 BCDB per package for now")
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
                try:
                    model_urls = self.bcdb.models_add(path)
                    for model_url in model_urls:
                        m = self.bcdb.model_get(url=model_url)
                        if model_url.startswith(self.name):
                            model_url2 = model_url[len(self.name) + 1 :]
                        else:
                            model_url2 = model_url
                        model_url3 = model_url2.replace(".", "__")
                        self._models[model_url3] = m
                except Exception as e:
                    self._models = None
                    md5 = generate_path_md5(path)
                    self._changes.remove(md5)
                    raise e
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
        self.load()
        path = self._changed("chatflows", die=False)
        if path:
            try:
                self._chatflows = self.gedis_server.chatbot.chatflows_load(path)
            except Exception as e:
                md5 = generate_path_md5(path)
                self._changes.remove(md5)
                raise e

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
                website_location = locations.get_location_spa(self.name)
            elif app_type == "html":
                website_location = locations.get_location_static(self.name)

            website_location.path_url = f"/{self.source.threebot}/{self.source.name}"
            website_location.use_jumpscale_weblibs = False
            fullpath = j.sal.fs.joinPaths(self.path, f"{app_type}/")
            website_location.path_location = fullpath

            # TODO: for now all packages are forced to https
            # if later we can customize to each package
            website_location.force_https = True

            locations.configure()
            website.configure()

    def _web_unload(self, app_type="frontend"):
        for port in (443, 80):
            website = self.openresty.get_from_port(port)
            locations = website.locations.get(f"{self.name}_locations_{port}")
            if app_type == "frontend":
                location = locations.get_location_spa(self.name)
                conf_location = locations.path_cfg_get(location.name)
            elif app_type == "html":
                location = locations.get_location_static(self.name)
                conf_location = locations.path_cfg_get(location.name)

            if conf_location:
                j.sal.fs.remove(conf_location)
            locations.delete()

    def config_load(self):
        self._log_info("load package.toml config", data=self)
        if self.giturl:
            self.path = j.clients.git.getContentPathFromURLorPath(self.giturl, branch=self.branch)
        tomlfile = f"{self.path}/package.toml"
        # print(f"tomfile: {tomlfile}")
        if not j.sal.fs.exists(tomlfile):
            self.delete()
            raise j.exceptions.Input(
                f"Failed to load package. package is corrupted.\
                            cannot find config file in path {tomlfile} for package {self.name}"
            )
        try:
            config = j.data.serializers.toml.loads(j.sal.fs.readFile(tomlfile))
            self._data._data_update(config)
        except Exception as e:
            self.delete()
            raise e

        if self.status == "init":  # should only move the config status if in init
            self.status = "config"
            self.save()

    def install(self, install_kwargs=None):
        # The installation parameters
        self.install_kwargs = install_kwargs or {}
        self._log_debug("install:%s" % self)
        self.load()
        if self.status != "config":  # make sure we load the config is not that state yet
            self.config_load()
        self._package_author.prepare()
        self.wiki_load(reset=True)
        if self.status != "installed":
            self.status = "installed"
            self.save()

    def start(self):
        self.load()
        if self.status == "toinstall":
            self.install()
        if self.status != "installed":
            self.install()
        self.actors_load()
        self._package_author.start()
        # self.wiki_load()  #when wiki is fixed we can do this & should do this
        if j.sal.fs.exists(f"{self.path}/frontend"):
            self._web_load(app_type="frontend")
        elif j.sal.fs.exists(f"{self.path}/html"):
            self._web_load(app_type="html")
        self.running = True
        self.save()

    def stop(self):
        self.load()
        self._package_author.stop()
        self.running = False
        self.status = "tostart"
        self.save()

    def uninstall(self):
        self.load()
        self.stop()
        self.load()
        # remove configuration for static and dynamic websites
        if j.sal.fs.exists(f"{self.path}/frontend"):
            self._web_unload(app_type="frontend")
        elif j.sal.fs.exists(f"{self.path}/html"):
            self._web_unload(app_type="html")
        # reload openresty to read the new configuration.
        self.openresty.reload()
        self.actors_remove()

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
