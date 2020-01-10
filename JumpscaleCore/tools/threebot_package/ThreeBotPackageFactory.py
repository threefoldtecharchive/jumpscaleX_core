from Jumpscale import j

from .ThreeBotPackage import ThreeBotPackage
from .ThreeBotPackageClient import ThreeBotPackageClient


class ThreeBotPackageFactory(j.baseclasses.object_config_collection_testtools):
    """
    deal with 3bot packages

    """

    __jslocation__ = "j.tools.threebot_packages"

    _SCHEMATEXT = """
        @url = jumpscale.threebot.package.1
        0:  name** = "main"
        1:  giturl = "" (S)  #if empty then local
        2:  branch = "" (S)
        3:  path = ""
        4:  status = "init,config,toinstall,installed,tostart,disabled,error" (E)
        5:  source = (O) !jumpscale.threebot.package.source.1
        6:  actor = (O) !jumpscale.threebot.package.actor.1
        7:  bcdbs = (LO) !jumpscale.threebot.package.bcdb.1


        @url = jumpscale.threebot.package.source.1
        0: name = ""
        1: threebot = ""
        2: description = ""
        3: version = "" (S)

        @url = jumpscale.threebot.package.actor.1
        0: namespace = ""

        @url = jumpscale.threebot.package.bcdb.1
        0: name = ""
        1: namespace = ""
        2: type = "zdb,sqlite,redis" (E)
        3: instance = "default"

        """

    def _childclass_selector(self, jsxobject, **kwargs):
        """
        allow custom implementation of which child class to use
        :return:
        """
        if j.threebot.active or j.data.bcdb._master:
            return ThreeBotPackage
        else:
            j.servers.threebot.threebotserver_require()
            return ThreeBotPackageClient

    def add_from_git(self, giturl=None, branch=None):
        """

        kosmos 'j.tools.threebot_packages.add_from_git()'

        :param giturl:
        :param branch:
        :return:
        """

        if not giturl:
            return self.add_from_git(
                "https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages"
            )
            # return self.add_from_git(
            #     "https://github.com/threefoldtech/jumpscaleX_core/tree/master/ThreeBotPackages"
            # )
        if not branch:
            branch = j.core.myenv.DEFAULT_BRANCH

        path = j.clients.git.getContentPathFromURLorPath(giturl, branch=branch)
        self.add(path=path)

    @property
    def names(self):
        res = []
        for x in self.find():
            res.append(x.name)
        res.sort()
        return res

    def add(self, path=None):
        """
        scan a path for package.toml and add all found packages
        :param path:
        :return:
        """
        path = j.core.tools.text_replace(path)
        if not path:
            # self.add("{DIR_CODE}/github/threefoldtech/jumpscaleX_core/ThreeBotPackages/")
            return self.add("{DIR_CODE}/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/")

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

    def test(self):
        """

        kosmos 'j.tools.threebot_packages.test()'

        :return:
        """
        # simulate we are a threebotserver
        j.servers.threebot._threebot_starting(False)
        self.add("{DIR_CODE}/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot")
        self.zerobot__chatbot_examples.reload()
        p = self.zerobot__chatbot_examples

        p = self.zerobot__base
        p.actors

        assert not p.models
        assert p.actors.system.ping() == "PONG"

        # p = self.tfgrid__gitea
        # p.models
