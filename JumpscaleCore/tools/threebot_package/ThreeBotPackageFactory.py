from Jumpscale import j

from .ThreeBotPackage import ThreeBotPackage


class ThreeBotPackageFactory(j.baseclasses.object_config_collection_testtools):
    """
    deal with 3bot packages

    """

    __jslocation__ = "j.tools.threebot_packages"
    _CHILDCLASS = ThreeBotPackage

    def add_from_git(self, giturl=None, branch=None):
        if not giturl:
            giturl = "https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages"
        if not branch:
            branch = j.core.myenv.DEFAULT_BRANCH

        path = j.clients.git.getContentPathFromURLorPath(giturl, branch=branch)
        self.add(path=path)

    def add(self, path=None):
        """
        scan a path for package.toml and add all found packages
        :param path:
        :return:
        """
        if not path:
            path = j.core.tools.text_replace("{DIR_CODE}/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/")

        def process(path, arg):
            basename = j.sal.fs.getBaseName(path)
            if basename == "package.toml":
                config = j.data.serializers.toml.loads(j.sal.fs.readFile(path))
                if "." in config["source"]["name"]:
                    raise j.exceptions.Input(". should not be in name", data=config)
                if not "source" in config:
                    raise j.exceptions.Input("could not find 'source' section in %s" % path)
                if not "threebot" in config["source"]:
                    raise j.exceptions.Input("could not find 'threebot' section in source section in %s" % path)
                name = config["source"]["threebot"].rstrip(".") + "." + config["source"]["name"]
                if True or not self.exists(name=name):
                    p = self.get(name=name, path=j.sal.fs.getDirName(path))
                    assert p.path

            return

        def callbackForMatchDir(path, arg):
            if j.sal.fs.getBaseName(path) in [
                "frontend",
                "node_modules",
                "packagemanagerui",
                "__pycache__",
                "wiki",
                "legacy",
                "actors",
                "models",
                "bottle",
                "html",
                "static",
                "src",
                "cypress",
                "views",
                "chatflows",
                "tests",
                "templates",
                "macros",
                "jobvis",
            ]:
                return False
            if not j.sal.fs.getBaseName(path).startswith("_"):
                print(" - %s" % path)
                return True
            # return j.sal.fs.exists(j.sal.fs.joinPaths(path, "package.py"))

        j.sal.fswalker.walkFunctional(path, callbackFunctionFile=process, callbackForMatchDir=callbackForMatchDir)

    def load(self, reset=False):
        """
        kosmos -p 'j.tools.threebot_packages.load(reset=True)'
        kosmos -p 'j.tools.threebot_packages.load()'
        """
        if reset:
            self.delete()
        wg = self.add_from_git()
