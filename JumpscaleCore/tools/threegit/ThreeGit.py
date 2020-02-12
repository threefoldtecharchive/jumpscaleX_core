from Jumpscale import j

from .Link import Linker
from .DocSite import DocSite, Doc


def load_wiki(wiki_name=None, wiki_path=None, reset=False):
    """
    loads any wiki and writes it do j.tools.threegit.docsites_path (/sandbox/var/docsites by default)
    we cannot use name parameter with myjobs.schedule, it has a name parameter itself
    """
    # use default path_dest
    if wiki_path.lower().strip().startswith("http"):
        threegit = j.tools.threegit.get_from_url(wiki_name, wiki_path)
    else:
        threegit = j.tools.threegit.get_from_path(wiki_name, wiki_path)
    threegit.process(reset=reset)
    threegit.save()


class ThreeGit(j.baseclasses.object_config):
    """
    To get wikis load faster by only loading git changes
    """

    _SCHEMATEXT = """
        @url = jumpscale.tools.threegit.1
        name** = "" (S)

        local_path = "" (S)
        # relative_base_path is the wiki directory inside local_path
        # if empty, then the local_path itself is the wiki directory
        relative_base_path = "" (S)
        dest_path = "" (S)
        revision = "" (S)
        uncommited_files = (LS)
        uncommited_files_revision = (S)
        """

    def _init(self, **kwargs):
        # self.dest = kwargs.get("dest", "")
        # self._macros_modules = {}  # key is the path
        # self._macros = {}  # key is the name
        # self._git_repos = {}
        self._docsite = None
        self._wiki_macros = None
        self._gitclient = None

    @property
    def source_path(self):
        return j.sal.fs.joinPaths(self.local_path, self.relative_base_path)

    @property
    def git_client(self):
        if not self._gitclient:
            path = j.clients.git.findGitPath(self.local_path, die=True)
            self._gitclient = j.clients.git.get(path)
        return self._gitclient

    @property
    def docsite(self):
        if self._docsite == None:
            self._docsite = DocSite(
                path=self.source_path,
                name=self.name,
                dest=self.dest_path,
                threegit=self,
                sonic_client=j.tools.threegit.sonic_client,
            )
        return self._docsite

    @property
    def wiki_macros(self):
        if self._wiki_macros == None:
            self._wiki_macros = j.tools.threegit._macros_load(self.source_path + "/wiki_macros")
        return self._wiki_macros

    def process(self, reset=False):
        """
        Process docsites it with macros, writes it to filesystem
        :return:
        """
        if self.docsite:
            self.docsite.write(reset=reset)
