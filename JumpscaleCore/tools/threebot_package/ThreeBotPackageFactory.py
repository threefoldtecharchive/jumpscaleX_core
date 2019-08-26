from Jumpscale import j

from .ThreeBotPackage import ThreeBotPackage


class ThreeBotPackageFactory(j.baseclasses.object_config_collection_testtools):
    """
    deal with 3bot packages

    """

    __jslocation__ = "j.tools.threebotpackage"
    _CHILDFACTORY_CLASS = ThreeBotPackage

    def test(self):
        """
        kosmos -p 'j.tools.threebotpackage.test()'
        """

        branch = j.core.myenv.DEFAULTBRANCH

        wg = self.get(
            name="test",
            giturl="https://github.com/threefoldtech/digitalmeX/tree/%s/threebot/packages/threefold/directory" % branch,
        )

        j.shell()
