from Jumpscale import j

from .ThreeBotPackage import ThreeBotPackage


class ThreeBotPackageFactory(j.baseclasses.object_config_collection_testtools):
    """
    deal with 3bot packages

    """

    __jslocation__ = "j.tools.threebot_packages"
    _CHILDCLASS = ThreeBotPackage

    def test(self):
        """
        kosmos -p 'j.tools.threebot_packages.test()'
        """

        wg = self.get(
            name="test",
            branch=j.core.myenv.DEFAULT_BRANCH,
            giturl="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/directory",
        )

        j.shell()
