from Jumpscale import j
from .Link import Linker

from .ThreeGit import ThreeGit


class ThreeGitFactory(j.baseclasses.object_config_collection):
    """
    To get wikis load faster by only loading git changes
    """

    __jslocation__ = "j.tools.threegit"
    _CHILDCLASS = ThreeGit

    def _init(self):
        self._docsites_path = j.sal.fs.joinPaths(j.dirs.VARDIR, "docsites")
        self._sonic = None
        self._wiki_macros = None

    @property
    def sonic_client(self):
        if not self._sonic:
            sonic_server = j.servers.sonic.get(name="threebot")
            self._sonic = j.clients.sonic.get(
                "threegit", password=sonic_server.adminsecret_, host=sonic_server.host, port=sonic_server.port
            )
        return self._sonic

    def docsite_get(self, path="", name="", pull=False):
        """
        loads docsite and process it with macros
        path: source of docsite
        name: name of docsite/wiki
        base_path: docsite/wiki dir inside the repo which has the md files will be joined with repo path
        pull: pull the docsite repo
        """
        if self.exists(name=name):
            return self.get(name=name).docsite

        if path.startswith("http"):
            # check if we already have a git repo, then the current checked-out branch
            repo_args = j.clients.git.getGitRepoArgs(path)
            host = repo_args[0]
            git_dest = repo_args[-3]
            repo_dest = j.clients.git.findGitPath(git_dest, die=False)
            if repo_dest:
                # replace branch with current one
                current_branch = j.clients.git.getCurrentBranch(repo_dest)
                path = Linker.replace_branch(path, current_branch, host)
        path = j.clients.git.getContentPathFromURLorPath(path, pull=pull)

        j.shell()
        tgit = self.get(name=name, path_source_wiki=path)

        return tgit.docsite

    @property
    def wiki_macros(self):
        if not self._wiki_macros:
            self._wiki_macros = self._macros_load()
        return self._wiki_macros

    def _macros_load(self, path=None):

        if not path:
            path = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), "macros")

        macros = j.baseclasses.dict()

        if j.sal.fs.exists(path):
            self._log_info("load macros:%s" % path)

            for path0 in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py", followSymlinks=True):
                name = j.sal.fs.getBaseName(path0)[:-3]  # find name, remove .py
                macros[name] = j.tools.jinja2.code_python_render(
                    obj_key=name, path=path0, reload=False, objForHash=name
                )

        return macros

    def get_docsite_path(self, name):
        return j.sal.fs.joinPaths(self.docsites_path, name)

    def test(self):
        """
        kosmos 'j.tools.threegit.test()'
        :return:
        """
        test_wiki = j.tools.threegit.get(
            name="test_wiki",
            path_source_wiki="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/docs/wikis/examples/docs/",
            path_dest_wiki="/tmp/test/test2",
        )
        test_wiki.process(reset=True)
        assert j.sal.fs.exists("/tmp/test/test2")
        # assert j.sal.fs.exists("/tmp/test/test2/.data") #we don't write data for now
        assert j.sal.fs.exists("/tmp/test/test2/test_gallery.md")
        assert j.sal.fs.exists("/tmp/test/test2/test_markdown.md")
        print("TEST OK")
