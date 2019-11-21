from Jumpscale import j

JSBASE = j.baseclasses.object


class ThreeGitFactory(j.baseclasses.object):
    """
    """

    __jslocation__ = "j.tools.threegit"

    def _init(self, **kwargs):
        pass

    def process(self, path=""):
        """

        :param path:
        :return:
        """
        j.shell()
