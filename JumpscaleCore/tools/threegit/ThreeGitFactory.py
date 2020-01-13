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
        self.docsites_path = j.sal.fs.joinPaths(j.dirs.VARDIR, "docsites")
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

    def find_git_path(self, path):
        return j.clients.git.findGitPath(path, die=False)

    def get_base_path(self, path):
        repo_local_path = self.find_git_path(path)
        base_path = path[len(repo_local_path) + 1 :]
        return repo_local_path, base_path

    def get_docsite_path(self, name):
        return j.sal.fs.joinPaths(self.docsites_path, name)

    def get_from_path(self, name, path):
        instance = self.get(name)
        repo_local_path, base_path = self.get_base_path(path)
        instance.local_path = repo_local_path
        instance.relative_base_path = base_path
        return instance

    def get_from_url(self, name, url, base_path="docs", pull=False):
        """gets an instance from a url, examples:
        https://github.com/threefoldtech/jumpscaleX_core
        https://github.com/threefoldtech/jumpscaleX_core/tree/development/sub_dir/wiki

        :param name: name of the instance
        :type name: str
        :param url: url
        :type url: str
        :param base_path: a relative base_path to this url, defaults to "docs"
        :type base_path: str, optional
        :param pull: if set, will clone/pull the repo, defaults to False
        :type pull: bool, optional
        :return: a threegit instance
        :rtype: ThreeGit
        """
        # first check if we have a local clone, then get the current checked-out branch
        # if not given in the url
        repo_args = j.clients.git.getGitRepoArgs(url)
        path = repo_args[-3]
        repo_local_path = self.find_git_path(path)
        # replace branch with current one
        current_branch = j.clients.git.getCurrentBranch(repo_local_path)
        url = Linker.replace_branch(url, current_branch, host=repo_args[0])

        # now get an instance
        path = j.clients.git.getContentPathFromURLorPath(url, pull=pull)
        instance = self.get_from_path(name, path)
        if not instance.relative_base_path:
            instance.relative_base_path = j.sal.fs.joinPaths(instance.relative_base_path, base_path)

        return instance

    def test(self):
        """
        kosmos 'j.tools.threegit.test()'
        :return:
        """
        test_wiki = j.tools.threegit.get(
            name="test_wiki",
            local_path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/docs/wikis/examples/docs/",
            dest_path="/tmp/test/test2",
        )
        test_wiki.process(reset=True)
        assert j.sal.fs.exists("/tmp/test/test2")
        # assert j.sal.fs.exists("/tmp/test/test2/.data") #we don't write data for now
        assert j.sal.fs.exists("/tmp/test/test2/test_gallery.md")
        assert j.sal.fs.exists("/tmp/test/test2/test_markdown.md")
        print("TEST OK")
