from Jumpscale import j

from .Link import Linker
from .DocSite import DocSite, Doc


def load_wiki(wiki_name=None, wiki_path=None, reset=False):
    """
    loads any wiki and writes it do j.tools.threegit.docsites_path (/sandbox/var/docsites by default)
    we cannot use name parameter with myjobs.schedule, it has a name parameter itself
    """
    # use default path_dest
    threegit = j.tools.threegit.get(name=wiki_name, path_sourc_wiki=wiki_path, path_dest="")
    threegit.process(reset=reset)
    threegit.save()


class ThreeGit(j.baseclasses.object_config):
    """
    To get wikis load faster by only loading git changes
    """

    _SCHEMATEXT = """
        @url = jumpscale.tools.threegit.1
        name** = "" (S)
        path_source = "" (S)
        path_source_wiki = ""
        path_dest_wiki = "" (S)
        """

    def _init(self, **kwargs):
        # self.dest = kwargs.get("dest", "")
        # self._macros_modules = {}  # key is the path
        # self._macros = {}  # key is the name
        # self._git_repos = {}
        self._docsite = None
        self._wiki_macros = None
        self._gitclient = None
        if not self.path_source and self.path_source_wiki:
            self.path_source = j.sal.fs.getParent(self.path_source_wiki)
        if not self.path_source_wiki:
            path = "%s/wiki" % (self.path_source)
            if j.sal.fs.exists(path):
                self.path_source_wiki = path

    @property
    def git_client(self):
        if not self._gitclient:
            path = j.clients.git.findGitPath(self.path_source, die=True)
            self._gitclient = j.clients.git.get(path)
        return self._gitclient

    @property
    def docsite(self):
        if self._docsite == None:
            if self.path_source_wiki:
                self._docsite = DocSite(
                    path=self.path_source_wiki,
                    name=self.name,
                    dest=self.path_dest_wiki,
                    threegit=self,
                    sonic_client=j.tools.threegit.sonic_client,
                )
        return self._docsite

    @property
    def wiki_macros(self):
        if self._wiki_macros == None:
            self._wiki_macros = j.tools.threegit._macros_load(self.path_source + "/wiki_macros")
        return self._wiki_macros

    def process(self, reset=False):
        """
        Process docsites it with macros, writes it to filesystem
        :return:
        """
        if self.docsite:
            self.docsite.write(reset=reset)
