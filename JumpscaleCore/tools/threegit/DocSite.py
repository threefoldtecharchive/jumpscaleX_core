import copy
import sys
import traceback

from urllib.parse import urlparse

from Jumpscale import j

from .Doc import Doc
from .Link import Linker, MarkdownLinkParser

JSBASE = j.baseclasses.object


class DocSite(j.baseclasses.object):
    """
    """

    def __init__(self, path, name="", dest="", sonic_client=None, threegit=None):
        JSBASE.__init__(self)
        self._j = j

        self.threegit = threegit
        self.path = path
        if not j.sal.fs.exists(path):
            raise j.exceptions.Base("Cannot find path:%s" % path)

        self.sonic_client = sonic_client
        self.name = j.core.text.strip_to_ascii_dense(name.lower())
        if not self.name:
            raise j.exceptions.Base("name cannot be empty")

        self._docs = {}
        self._files = {}
        self._sidebars = {}

        self._errors = []

        self.links_verify = False

        self.outpath = dest or j.tools.threegit.get_docsite_path(self.name)
        j.sal.fs.createDir(self.outpath)

        self.error_file_path = f"{self.outpath}/errors.md"

        self._log_level = 1

        self._git = None
        self._loaded = False

        # add git changed files
        self.revision = None
        self._files_changed = None

        self._log_info("found:%s" % self)

    def _clean(self, name):
        assert j.data.types.string.check(name)
        #     if len(name)==1:
        #         name=name[0]
        #     else:
        #         name="/".join(name) #not sure this is correct
        return j.core.text.convert_to_snake_case(name)

    # @classmethod
    # def get_from_name(cls, name):
    #     name = prepare_name(name)
    #     meta_path = f"{cls.outpath}/.data"
    #     repo_meta = j.sal.fs.readFile(meta_path).decode()
    #     repo_data = j.data.serializers.json.loads(repo_meta)
    #     repo_args = j.clients.git.getGitRepoArgs(repo_data["repo"])
    #     path = j.sal.fs.joinPaths(repo_args[-3], repo_data.get("base_path", ""))
    #
    #     return cls(name=name, path=path)

    @property
    def host(self):
        return urlparse(self.metadata["repo"]).hostname

    @property
    def git(self):
        return self.threegit.git_client

    @property
    def account(self):
        return self.git and self.git.account

    @property
    def repo(self):
        return self.git and self.git.name

    @property
    def branch(self):
        return self.git and self.git.branchName

    def is_different_source(self, custom_link):
        """check if account, repo or branch are differnt from current docsite

        :param custom_link: instanc of CustomLink
        :type custom_link: CustomLink
        :return: True if different, False if the same
        :rtype: bool
        """
        return (
            custom_link.account
            and custom_link.account != self.account
            or custom_link.repo
            and custom_link.repo != self.repo
            or custom_link.branch
            and custom_link.branch != self.branch
        )

    def get_real_source(self, custom_link, host=None):
        """
        get the source of the data (only works for github and local paths for now)

        :param custom_link: custom link
        :type custom_link: CustomLink
        :param host: host, defaults to githib.com
        :type host: str
        :return: a path or a full link
        :rtype: str
        """
        if custom_link.is_url:
            # as-is
            return custom_link.path

        account = custom_link.account or self.account
        repo = custom_link.repo or self.repo
        if not host:
            host = "github.com"

        linker = Linker(host, account, repo)

        if custom_link.reference:
            return linker.issue(custom_link.reference)

        same_repo = account == self.account and repo == self.repo
        if same_repo:
            # the same docsite, the same internal link
            # also, custom link branch is ignored here
            return custom_link.path

        branch = custom_link.branch
        return linker.tree(custom_link.path, branch=branch)

    def get_real_link(self, custom_link, host=None):
        """
        get real link of custom link as a url
        """
        repo = self.get_real_source(custom_link, host)
        if not MarkdownLinkParser(repo).is_url:
            # not an external url, it's a relative link inside this docsite, keep as is
            return custom_link.path
        else:
            # the real source is a url outside this docsite
            # get a new link and docsite
            host = j.clients.git.getGitRepoArgs(repo)[0]
            new_link = Linker.to_custom_link(repo, host)
            # to match any path, start with root `/`
            url = Linker(host, new_link.account, new_link.repo).tree("/")
            docsite = j.tools.threegit.get_from_url(new_link.repo, url, base_path="").docsite
            custom_link = new_link

        docsite.load(reset=True)

        try:
            included_doc = docsite.doc_get(custom_link.path)
            full_path = included_doc.path
        except j.exceptions.Base:
            full_path = docsite.file_get(custom_link.path)

        path = full_path.replace(j.clients.git.findGitPath(full_path), "")
        return Linker(custom_link.host, custom_link.account, custom_link.repo).tree(path, branch=custom_link.branch)

    @property
    def urls(self):
        urls = [item for item in self.docs.keys()]
        urls.sort()
        return urls

    @property
    def docs(self):
        return self._docs

    @property
    def files(self):
        return self._files

    @property
    def docsite_dir_has_files(self):
        return j.sal.fs.listFilesInDir(self.outpath)

    def load(self, reset=False):
        """
        walk in right order over all files which we want to potentially use (include)
        and remember their paths

        if duplicate only the first found will be used
        """
        # if not self.docsite_dir_has_files:
        #     reset = True

        if not reset and self._loaded:
            return

        self.revision = self.threegit.git_client.config_3git_set("revision_last_processed_docsite", "")

        path = self.path
        if not j.sal.fs.exists(path=path):
            raise j.exceptions.NotFound("Cannot find source path in load:'%s'" % path)

        j.sal.fs.remove(self.error_file_path)

        def callbackForMatchFile(path, arg):
            base = j.sal.fs.getBaseName(path).lower()
            if base == "errors.md":
                return False
            if base == "_sidebar.md":
                return True
            if base.startswith("_"):
                return False
            ext = j.sal.fs.getFileExtension(path)
            if ext == "md" and base[:-3] in ["summary", "default"]:
                return False
            return True

        def callbackFunctionFile(path, arg):
            if path.find("error.md") != -1:
                return
            self._log_debug("file:%s" % path)
            ext = j.sal.fs.getFileExtension(path).lower()
            base = j.sal.fs.getBaseName(path)
            if ext == "md":
                self._log_debug("found md:%s" % path)
                base = base[:-3]  # remove extension
                doc = Doc(path, base, docsite=self, sonic_client=self.sonic_client)
                self._docs[doc.name_dot_lower] = doc
            else:
                self.file_add(path)

        if not reset:
            # check changed files and process it using 3git tool
            self.revision = self.threegit.git_client.config_3git_get("revision_last_processed_docsite")
            revision, self._files_changed, old_files = self.threegit.git_client.logChanges(
                path=self.path, from_revision=self.revision, untracked=True
            )
        else:
            self._files_changed = j.sal.fs.listFilesInDir(self.path, recursive=True)
            revision = self.threegit.git_client.config_3git_get("revision_last_processed_docsite")
            old_files = None

        for item in self._files_changed:
            if not reset:
                item = f"{self.threegit.git_client.path}/{item}"
            if j.sal.fs.exists(item):
                if j.sal.fs.isFile(item):
                    if callbackForMatchFile(item, ""):
                        callbackFunctionFile(item, "")
        if old_files:
            for ditem in old_files:
                item_path = j.sal.fs.joinPaths(self.outpath, ditem)
                j.sal.fs.remove(item_path)

        self.threegit.git_client.logChangesRevisionSet(revision)
        print("git revision set with value: ", revision)
        self._loaded = True

    def file_add(self, path, duplication_test=False):
        ext = j.sal.fs.getFileExtension(path).lower()
        base = j.sal.fs.getBaseName(path)
        if ext in [
            "png",
            "jpg",
            "jpeg",
            "pdf",
            "docx",
            "doc",
            "xlsx",
            "xls",
            "ppt",
            "pptx",
            "mp4",
            "css",
            "js",
            "mov",
            "py",
            "svg",
            "json",
        ]:
            self._log_debug("found file:%s" % path)
            base = self._clean(base)
            if duplication_test and base in self._files:
                raise j.exceptions.Input(message="duplication file in %s,%s" % (self, path))
            self._files[base] = path

    def error_raise(self, errormsg, doc=None):
        if doc is not None:
            errormsg2 = "## ERROR: %s\n\n- in doc: %s\n\n%s\n\n\n" % (doc.name, doc, errormsg)
            key = j.data.hash.md5_string("%s_%s" % (doc.name, errormsg))
            if not key in self._errors:
                errormsg3 = "```\n%s\n```\n" % errormsg2
                j.sal.fs.writeFile(self.error_file_path, errormsg3, append=True)
                self._log_error(errormsg2)
                doc.errors.append(errormsg)
        else:
            self._log_error("DEBUG NOW raise error")
            raise j.exceptions.Base("stop debug here")

    def file_get(self, name, die=True):
        """
        returns path to the file
        """
        name = self._clean(name)

        if name in self.files:
            return self.files[name]

        name = name.replace(j.sal.fs.getFileExtension(name), "")
        for path in self.files.values():
            partial_path = path.lower().replace(j.sal.fs.getFileExtension(path), "")
            if partial_path.endswith(name):
                return path

        if die:
            raise j.exceptions.Input(message="Did not find file:%s in %s" % (name, self))
        return None

    def html_get(self, name, cat="", die=True):
        doc = self.doc_get(name=name, cat=cat, die=die)
        return doc.html_get()

    def doc_get(self, name, cat="", die=True):

        if j.data.types.list.check(name):
            name = "/".join(name)

        name = name.replace("/", ".").strip(".")

        name = self._clean(name)

        name = name.strip("/")
        name = name.lower()

        if name.endswith(".md"):
            name = name[:-3]  # remove .md

        if "/" in name:
            name = name.replace("/", ".")

        name = name.strip(".")  # lets make sure its clean again

        # let caching work
        if name in self.docs:
            if self.docs[name] is None and die:
                raise j.exceptions.Input(message="Cannot find doc with name:%s" % name)
            return self.docs[name]

        # build candidates to search
        candidates = [name]
        if name.endswith("readme"):
            candidates.append(name[:-6] + "index")
        else:
            candidates.append(name + ".readme")

        if name.endswith("index"):
            nr, res = self._doc_get(name[:-5] + "readme", cat=cat)
            if nr == 1:
                return 1, res
            name = name[:-6]
        else:
            candidates.append(name + ".index")

        # look for $fulldirname.$dirname as name of doc
        if "." in name:
            name0 = name + "." + name.split(".")[-1]
            candidates.append(name0)

        for cand in candidates:
            nr, res = self._doc_get(cand, cat=cat)
            if nr == 1:
                self.docs[name] = res  # remember for caching
                return self.docs[name]
            if nr > 1:
                self.docs[name] = None  # means is not there
                break

        if die:
            raise j.exceptions.Input(message="Cannot find doc with name:%s (nr docs found:%s)" % (name, nr))
        else:
            return None

    def _doc_get(self, name, cat=""):

        if name.lower().startswith("_sidebar_parent"):
            return 1, ""

        if name in self.docs:
            if cat is "":
                return 1, self.docs[name]
            else:
                if self.docs[name] == cat:
                    return 1, self.docs[name]

        else:

            res = []
            for key, item in self.docs.items():
                if item is None or item == "":
                    continue
                if item.name_dot_lower.endswith(name):
                    res.append(key)
            if len(res) > 0:
                return len(res), self.docs[res[0]]
            else:
                return 0, None

    def sidebar_get(self, url, reset=False):
        """
        will calculate the sidebar, if not in url will return None
        """
        self.load(reset=reset)
        if j.data.types.list.check(url):
            url = "/".join(url)
        self._log_debug("sidebar_get:%s" % url)
        if url in self._sidebars:
            return self._sidebars[url]

        url_original = copy.copy(url)
        url = url.strip("/")
        url = url.lower()

        if url.endswith(".md"):
            url = url[:-3]

        url = url.replace("/", ".")
        url = url.strip(".")

        url = self._clean(url)

        if url == "":
            self._sidebars[url_original] = None
            return None

        if "_sidebar" not in url:
            self._sidebars[url_original] = None
            return None  # did not find sidebar just return None

        if url in self.docs:
            self._sidebars[url_original] = self._sidebar_process(self.docs[url].markdown, url_original=url_original)
            return self._sidebars[url_original]

        # did not find the usual location, lets see if we can find the doc allone
        url0 = url.replace("_sidebar", "").strip().strip(".").strip()
        if "." in url0:  # means we can
            name = url0.split(".")[-1]
            doc = self.doc_get(name, die=False)
            if doc:
                # we found the doc, so can return the right sidebar
                possiblepath = doc.path_dir_rel.replace("/", ".").strip(".") + "._sidebar"
                if not possiblepath == url:
                    return self.get(possiblepath)

        # lets look at parent
        print("need to find parent for sidebar")

        if url0 == "":
            print("url0 is empty for sidebar")
            raise j.exceptions.Base("cannot be empty")

        newurl = ".".join(url0.split(".")[:-1]) + "._sidebar"
        newurl = newurl.strip(".")
        return self.sidebar_get(newurl)

    def _sidebar_process(self, c, url_original):
        def clean(c):
            out = ""
            state = "start"
            for line in c.split("\n"):
                lines = line.strip()
                if lines.startswith("*"):
                    lines = lines[1:]
                if lines.startswith("-"):
                    lines = lines[1:]
                if lines.startswith("+"):
                    lines = lines[1:]
                lines = lines.strip()
                if lines == "":
                    continue
                if line.find("(/)") is not -1:
                    continue
                if line.find("---") is not -1:
                    if state == "start":
                        continue
                    state = "next"
                out += line + "\n"
            return out

        c = clean(c)

        out = "* **[Wiki (home)](/)**\n"

        for line in c.split("\n"):
            if line.strip() == "":
                out += "\n\n"
                continue

            if "(" in line and ")" in line:
                url = line.split("(", 1)[1].split(")")[0]
            else:
                url = ""
            if "[" in line and "]" in line:
                descr = line.split("[", 1)[1].split("]")[0]
                pre = line.split("[")[0]
                pre = pre.replace("* ", "").replace("- ", "")
                if url == "":
                    url = descr
            else:
                descr = line
                pre = "<<"

            if url:
                doc = self.doc_get(url, die=False)
                if doc is None:
                    out += "    %s* NOTFOUND:%s" % (pre, url)
                else:
                    out += "    %s* [%s](/%s)\n" % (pre, descr, doc.name_dot_lower.replace(".", "/"))

            else:
                if not pre:
                    pre = "    "
                if pre is not "<<":
                    out += "    %s* %s\n" % (pre, descr)
                else:
                    out += "    %s\n" % (descr)

        res = self.doc_get("_sidebar_parent", die=False)
        if res:
            out += res.content
        else:
            # out+="----\n\n"
            out += "\n\n* **Wiki Sites.**\n"
            keys = [item for item in j.tools.threegit.docsites.keys()]
            keys.sort()
            for key in keys:
                if key.startswith("www") or key.startswith("simple"):
                    continue
                if len(key) < 4:
                    continue
                out += "    * [%s](../%s/)\n" % (key, key)

        return out

    def verify(self, url_check=False):
        keys = [item for item in self.docs.keys()]
        keys.sort()
        for key in keys:
            doc = self.doc_get(key, die=True)
            self._log_info("verify:%s" % doc)
            try:
                doc.markdown  # just to trigger the error checking
            except Exception as e:
                msg = "unknown error to get markdown for doc, error:\n%s\n%s" % (e, traceback.format_exc())
                self.error_raise(msg, doc=doc)
            # doc.html
        return self.errors

    @property
    def errors(self):
        """
        return current found errors
        """
        errors = "DID NOT FIND ERRORSFILE, RUN js_doc verify in the doc directory"
        if j.sal.fs.exists(self.error_file_path):
            errors = j.sal.fs.readFile(self.error_file_path)
        return errors

    def __repr__(self):
        return "docsite:%s" % (self.path)

    __str__ = __repr__

    def write_metadata(self):
        # Create file with extra content to be loaded in docsites
        data = {"name": self.name, "repo": "", "base_path": self.threegit.relative_base_path}

        if self.git:
            data["repo"] = "https://github.com/%s/%s" % (self.account, self.repo)

        data_json = j.data.serializers.json.dumps(data)
        j.sal.fs.writeFile(self.metadata_path, data_json, append=False)
        j.sal.fs.createDir(self.outpath)
        j.sal.fs.writeFile(self.metadata_path, data_json, append=False)

    @property
    def metadata(self):
        return j.data.serializers.json.loads(j.sal.fs.readFile(self.metadata_path))

    @property
    def metadata_path(self):
        return self.outpath + "/.data"

    def write(self, reset=False, url_check=False):
        if reset:
            j.sal.fs.remove(self.outpath)

        self.load(reset=reset)
        # self.verify(url_check=url_check)

        j.sal.fs.createDir(self.outpath)

        self.write_metadata()

        keys = [item for item in self.docs.keys()]
        keys.sort()
        for key in keys:
            doc = self.doc_get(key, die=False)
            if doc:
                doc.write()
