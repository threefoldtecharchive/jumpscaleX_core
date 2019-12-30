from Jumpscale import j

from .Link import Linker
from .DocSite import DocSite, Doc


def load_wiki(wiki_name=None, wiki_path=None, reset=False):
    """loads any wiki and writes it do /docsites we cannot use name parameter with myjobs.schedule, it has a name parameter itself"""
    path_dest = f"/docsites/{wiki_name}"

    threegit_tool = j.tools.threegit.get(name=wiki_name, path_source=wiki_path, path_dest=path_dest)
    j.sal.fs.createDir(path_dest)

    threegit_tool.process(reset=reset)


class ThreeGit(j.baseclasses.object_config):
    """
    To get wikis load faster by only loading git changes
    """

    _SCHEMATEXT = """
        @url = jumpscale.tools.threegit.1
        name** = "" (S)
        path_source = "" (S)
        path_dest = "" (S)
        """

    def _init(self, **kwargs):
        self.dest = kwargs.get("dest", "")
        self._macros_modules = {}  # key is the path
        self._macros = {}  # key is the name
        self.docsites = {}
        self._git_repos = {}

    def macros_load(self, path=None):
        """load all macros code dynamically"""
        self._log_info("load macros...")

        if not path:
            path = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), "macros")

        if path not in self._macros_modules:

            if not j.sal.fs.exists(path=path):
                raise j.exceptions.Input("Cannot find path:'%s' for macro's, does it exist?" % path)

            for path0 in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py", followSymlinks=True):
                name = j.sal.fs.getBaseName(path0)[:-3]  # find name, remove .py
                self._macros[name] = j.tools.jinja2.code_python_render(
                    obj_key=name, path=path0, reload=False, objForHash=name
                )

    def find_docs_path(self, path, base_path="docs"):
        """try to find docs path from base_path inside a given repo path and return it if exists

        :param path: path, e.g. `/sandbox/code/github/threefoldfoundation/info_foundation`
        :param base_path: dir inside the repo which has the md files will be joined with repo path
        :type path: str
        """
        gitpath = j.clients.git.findGitPath(path)
        if not gitpath or gitpath != path:
            return path

        docs_path = j.sal.fs.joinPaths(path, base_path)
        if j.sal.fs.exists(docs_path):
            return docs_path
        return path

    def _git_get(self, path):
        """
        git the git client used for 3git log tools
        param: path: path of the docsite repo
        """
        if path not in self._git_repos:
            try:
                gc = j.clients.git.get(path, check_path=False)
            except Exception as e:
                self._log_error(f"error while get git of {path}", exception=e)
                return
            self._git_repos[path] = gc
        return self._git_repos[path]

    def load(self, path="", name="", dest="", base_path="docs", pull=False):
        """
        loads docsite and process it with macros
        path: source of docsite
        dest: dest of output processed files
        name: name of docsite/wiki
        base_path: docsite/wiki dir inside the repo which has the md files will be joined with repo path
        pull: pull the docsite repo
        """
        self.macros_load()
        if path.startswith("http"):
            # check if we already have a git repo, then the current checked-out branch
            repo_args = j.clients.git.getGitRepoArgs(path)
            host = repo_args[0]
            dest = repo_args[-3]
            repo_dest = j.clients.git.findGitPath(dest, die=False)
            if repo_dest:
                # replace branch with current one
                current_branch = j.clients.git.getCurrentBranch(repo_dest)
                path = Linker.replace_branch(path, current_branch, host)
            path = self.find_docs_path(j.clients.git.getContentPathFromURLorPath(path, pull=pull), base_path)

        sonic_server = j.servers.sonic.get(name="threebot")
        sonic_cl = j.clients.sonic.get(
            "threegit", password=sonic_server.adminsecret_, host=sonic_server.host, port=sonic_server.port
        )
        ds = DocSite(path=path, name=name, dest=dest, threegit=self, sonic_client=sonic_cl)
        self.docsites[ds.name] = ds
        return self.docsites[ds.name]

    def process(self, check=True, reset=False):
        """
        Process docsites it with macros, writes it to filesystem
        :param check: reload changed files in docsite since last revision
        :param force: Reload all docsites files and reparse them
        :return:
        """
        docsite = self.load(name=self.name, path=self.path_source, dest=self.path_dest, base_path="docs")
        docsite.write(check=check, reset=reset)
        print("LOADING DONE")
