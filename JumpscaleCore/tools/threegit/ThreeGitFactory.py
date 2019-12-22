from Jumpscale import j


from .ThreeGit import ThreeGit


class ThreeGitFactory(j.baseclasses.object_config_collection):
    """
    To get wikis load faster by only loading git changes
    """

    __jslocation__ = "j.tools.threegit"
    _CHILDCLASS = ThreeGit

    def test(self):
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
