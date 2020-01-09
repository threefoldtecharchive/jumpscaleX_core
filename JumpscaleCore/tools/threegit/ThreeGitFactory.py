from Jumpscale import j


from .ThreeGit import ThreeGit


class ThreeGitFactory(j.baseclasses.object_config_collection):
    """
    To get wikis load faster by only loading git changes
    """

    __jslocation__ = "j.tools.threegit"
    _CHILDCLASS = ThreeGit

    def _init(self):
        self.docsites_path = j.sal.fs.joinPaths(j.dirs.VARDIR, "docsites")

    def get_docsite_path(self, name):
        return j.sal.fs.joinPaths(self.docsites_path, name)

    def test(self):
        """
        kosmos 'j.tools.threegit.test()'
        :return:
        """
        test_wiki = j.tools.threegit.get(
            name="test_wiki",
            path_source="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/docs/wikis/examples/docs/",
            path_dest="/test/test2",
        )
        test_wiki.process(check=True)
        assert j.sal.fs.exists("/test/test2")
        assert j.sal.fs.exists("/test/test2/.data")
        assert j.sal.fs.exists("/test/test2/test_gallery.md")
        assert j.sal.fs.exists("/test/test2/test_markdown.md")
        print("TEST OK")
