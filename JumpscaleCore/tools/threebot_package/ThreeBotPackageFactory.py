from Jumpscale import j

from .ThreeBotPackage import ThreeBotPackage


class ThreeBotPackageFactory(j.baseclasses.object_config_collection_testtools):
    """
    deal with 3bot packages

    """

    __jslocation__ = "j.tools.threebotpackage"
    _CHILDCLASS = ThreeBotPackage

    def test(self):
        """
        kosmos -p 'j.tools.threebotpackage.test()'
        """

        wg = self.get(
            name="test",
            branch=j.core.myenv.DEFAULTBRANCH,
            giturl="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/directory",
        )

        j.shell()
