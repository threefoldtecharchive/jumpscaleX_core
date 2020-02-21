import toml
import re
import copy
import io

from urllib.parse import urlparse
from Jumpscale import j

JSBASE = j.baseclasses.object


# Some links that needs to be skipped from verifying because the crawling is forbidden
SKIPPED_LINKS = [
    "t.me",
    "chat.grid.tf",
    "linkedin.com",
    "docs.grid.tf",
    "btc-alpha",
    "kraken.com",
    "bitoasis.net",
    "cex.io",
    "itsyou.online",
    "skype:",
    "medium.com",
    "mailto:",
]


class MarkdownLinkParser:
    """A link with custom format of `account:repo(branch):path`

    THIS IS A PARSER FOR THE MARKDOWN LINKS

    account, repo and branch are optional, examples:

    threefoldtech:jumpscaleX(development):docs/readme.md
    jumpscaleX(development):docs/readme.md
    jumpscaleX:docs/readme.md
    jumpscaleX:#123
    docs/readme.md
    #124
    http://github.com/account/repo/tree/master/docs/readme.md
    """

    URL_RE = re.compile(r"^(http|https)\:\/\/", re.IGNORECASE)
    REFERENCE_RE = re.compile(r"^\#(\d+)$")
    REPO_PATH_RE = re.compile(
        r"""
        ^                   # start of the line/string
        (?:                 # non-capturing group
            (.*?)           # match any char -> repo
            (?:             # non-capturing group
                \(          # anything between (...)
                    (.*?)   # in a group -> branch
                \)
            )?              # optional
            \:              # match literal :
        )?                  # optional
        (.*?)               # anything at the end after that -> path
        (?:
            \!\s*?
            (\w+)           # any marker (part) like !A
        )?$                 # optional
    """,
        re.X,
    )

    def __init__(self, link, **kwargs):
        self.link = link.strip()
        self.host = None
        self.account = None
        self.repo = None
        self.branch = None
        self.marker = None  # part

        if self.is_url:
            self.path = link
        else:
            self.host, self.account, other_part = self.get_host_and_account()
            self.repo, branch, self.path, self.marker = self.parse_repo_and_path(other_part)
            self.branch = branch or self.branch

    def get_host_and_account(self):
        """get host, account and other part

        :return: a tuple of (host, account, other_part), host and account can be None
        :rtype: tuple
        """
        link = self.link
        host = None

        if link.count(":") == 3:
            host, _, link = self.link.partition(":")

        if link.count(":") == 2:
            account, _, other_part = link.partition(":")
            return host, account, other_part

        return None, None, self.link

    def parse_repo_and_path(self, repo_and_path):
        """parse the repo and path part, repo(branch):path
        possible examples, `repo(branch):path`, `repo:path` and `path`.

        :param repo_and_path: containing possible format
        :type repo_and_path: str
        :return: a tuple of (repo, branch, path), repo and branch can be None
        :rtype: tuple
        """
        return self.REPO_PATH_RE.match(repo_and_path).groups()

    @property
    def is_url(self):
        """check if the given links is a url

        :return: True if a url, False otherwise
        :rtype: bool
        """
        return bool(self.URL_RE.match(self.link))

    @property
    def reference(self):
        """return the reference id of the given link

        :return: id or None
        :rtype: str
        """
        id_match = self.REFERENCE_RE.match(self.path)
        if id_match:
            return id_match.group(1)

    @property
    def is_reference(self):
        """check if the given link is a reference (e.g. #124)

        :return: True if a reference, False otherwise
        :rtype: bool
        """
        return bool(self.reference)

    @classmethod
    def test(cls):
        l = MarkdownLinkParser("threefoldtech:jumpscaleX(dev):#124")
        assert l.account == "threefoldtech"
        assert l.repo == "jumpscaleX"
        assert l.branch == "dev"
        assert l.path == "#124"

        l = MarkdownLinkParser("jumpscaleX(dev):docs/test.md")
        assert l.repo == "jumpscaleX"
        assert l.branch == "dev"
        assert l.path == "docs/test.md"

        l = MarkdownLinkParser("docs/test.md")
        assert not l.account
        assert not l.repo
        assert l.path == "docs/test.md"

        l = MarkdownLinkParser("github.com:threefoldtech:jumpscaleX(dev):docs/test.md")
        assert l.host == "github.com"
        assert l.repo == "jumpscaleX"
        assert l.branch == "dev"
        assert l.path == "docs/test.md"

    def __str__(self):
        if not self.repo:
            out = "custom link: %s" % self.path
        else:
            out = "custom link: %s(%s):%s" % (self.repo, self.branch, self.path)
        return out

    __repr__ = __str__


class Linker:
    """
    A genric linker
    """

    ISSUE = "issues/{id}"
    PULL_REQUEST = "pull/{id}"
    TREE = "tree/{branch}"

    REPO_LINK_RE = r"""
        (?:http|https)\:\/\/{host}                         # e.g. github
        (?:\/([^\/]+))                                  # account
        (?:\/([^\/]+))                                  # repo
        (?:                                             # a link to tree/blob
            \/
            (?:tree|blob)
            \/
            ([^\/]+)                                    # branch
            (?:                                         # possible path
                \/
                (.*?)$
            )?
        )?
    """

    def __init__(self, host, account, repo):
        if not host:
            host = "github.com"
        self.host = host.lower()
        if not self.host.startswith("http"):
            self.host = "https://" + self.host

        self.account = account
        self.repo = repo

    @classmethod
    def remove_slash(self, arg):
        return arg.lstrip("/")

    @classmethod
    def join_parts(cls, *args):
        args = [cls.remove_slash(arg) for arg in args]
        return j.sal.fs.joinPaths(*args)

    def join_with_host(self, *args):
        if self.host:
            args = (self.host, *args)
        return self.join_parts(*args)

    def join(self, *args):
        return self.join_with_host(self.account, self.repo, *args)

    def issue(self, _id):
        return self.join(self.ISSUE.format(id=_id))

    def pull_request(self, _id):
        return self.join(self.PULL_REQUEST.format(id=_id))

    def tree(self, path, branch=None):
        if not branch:
            branch = "master"
        return self.join(self.TREE.format(branch=branch), path)

    @classmethod
    def get_repo_re(cls, host):
        return re.compile(cls.REPO_LINK_RE.format(host=host), re.X | re.IGNORECASE)

    @classmethod
    def to_custom_link(cls, url, host=None):
        if not host:
            try:
                host = j.clients.git.getGitRepoArgs(url)[0]
            except j.exceptions.Base:
                host = "github.com"

        match = cls.get_repo_re(host).match(url)
        if not match:
            raise j.exceptions.Value(f"not a valid {host} url: '{url}'")

        account, repo, branch, path = match.groups()
        link = f"{host}:{account}:{repo}"
        if branch:
            link += f"({branch})"
        if not path:
            path = ""
        link += f":{path}"
        return MarkdownLinkParser(link)

    @classmethod
    def replace_branch(cls, url, to_branch, host):
        tmp = cls.to_custom_link(url, host)
        return cls(host, tmp.account, tmp.repo).tree(tmp.path, to_branch)


class Link(j.baseclasses.object):
    LINK_MARKDOWN_PATTERN = r"""
        \!?                         # match optiona !
        \[                          # start of descirption [
            (
                [^\]\(]+            # match anything other than ] or ( -> description text
            )?                      # optional
        \]                          # end of description
        \(                          # start of link
            (                       # -> full link text
                [^\(\)]*?           # anything other than ( or )
                (?:                 # possible one non-capturing group of (...) for the branch
                    \(              # match literal (
                        [^\(\)]*?   # match anything other than ( or )
                    \)              # match literal )
                )?
                [^\(\)]*?           # anything other than ( or )
            )??                     # optional
        \)                          # end of link
    """
    LINK_MARKDOWN_RE = re.compile(LINK_MARKDOWN_PATTERN, re.X)

    def __init__(self, doc, source):
        JSBASE.__init__(self)
        self.docsite = doc.docsite
        self.doc = doc
        self.extension = ""
        self.source = source  # original text
        self.cat = ""  # category in image,doc,link,officedoc, imagelink  #doc is markdown
        self.link_source = ""  # text to replace when rewrite is needed
        self.link_source_original = ""  # original link
        self.error_msg = ""
        self.filename = ""
        self.filepath = ""
        self.link_descr = ""  # whats inside the []
        self.link_to_doc = None
        self._process()

    def _clean(self, name):
        return j.core.text.convert_to_snake_case(name)

    def error(self, msg):
        self.error_msg = msg
        msg = "**ERROR:** problem with link:%s\n%s" % (self.source, msg)
        # self._log_error(msg)
        self.docsite.error_raise(msg, doc=self.doc)
        self.doc._content = self.doc._content.replace(self.source, msg)
        return msg

    def remove_quotes(self, s):
        if s:
            return s.replace('"', "").replace("'", "")
        return ""

    def parse_markdown(self, link_markdown):
        match = self.LINK_MARKDOWN_RE.match(link_markdown)
        if match:
            match = match.groups()
            return map(self.remove_quotes, match)
        raise j.exceptions.Value("not a link markdown")

    def get_docsite(self, external_link, name):
        url = urlparse(external_link)
        path = url.path

        if not j.sal.fs.getFileExtension(path):
            parent_dir = external_link
        else:
            parent_path = j.sal.fs.getDirName(path)
            parent_dir = Linker.join_parts("https://", url.hostname, parent_path)

        new_docsite = j.tools.markdowndocs.load(parent_dir, name=name)
        new_docsite.write()
        return new_docsite

    def _process(self):
        self.link_descr, self.link_source = self.parse_markdown(self.source)
        if self.should_skip():
            return

        if self.link_source.strip() == "":
            return self.error("link is empty, but url is:%s" % self.source)

        if "@" in self.link_descr:
            self.link_source_original = self.link_descr.split("@")[1].strip()  # was link to original source
            self.link_descr = self.link_descr.split("@")[0].strip()

        if not self.link_source.lower().strip().startswith("http"):
            custom_link = MarkdownLinkParser(self.link_source)
            try:
                self.link_source = self.docsite.get_real_link(custom_link, custom_link.host)
            except ValueError as e:
                self.doc.error_raise(f"cannot get a real link of {self.link_source}\n{e}")
        # if "?" in self.link_source:
        #     lsource = self.link_source.split("?", 1)[0]
        # else:
        #     lsource = self.link_source

        path = urlparse(self.link_source).path
        if path:
            self.extension = j.sal.fs.getFileExtension(path)

        if "http" in self.link_source or "https" in self.link_source:
            self.link_source_original = self.link_source
            if self.source.startswith("!"):
                if "?" in self.link_source:
                    link_source = self.link_source.split("?", 1)[0]
                else:
                    link_source = self.link_source
                self.filename = self._clean(j.sal.fs.getBaseName(link_source))

                if not self.extension in ["png", "jpg", "jpeg", "mov", "mp4", "mp3", "docx"]:
                    self.extension = "jpeg"  # to support url's like https://images.unsplash.com/photo-1533157961145-8cb586c448e1?ixlib=rb-0.3.5&ixid=eyJhcHBfaWQiOjEyMDd9&s=4e252bcd55caa8958985866ad15ec954&auto=format&fit=crop&w=1534&q=80
                    self.filename = self.filename + ".jpeg"

                if j.sal.fs.getFileExtension(self.filename) != self.extension:
                    j.shell()
            else:
                # check link exists
                self.cat = "link"
                if self.docsite.links_verify:
                    self.link_verify()
        else:
            if self.link_source.strip() == "/":
                self.link_source = ""
                return
            if "#" in self.link_source:
                self.link_source = ""
                return

            if "?" in self.link_source:
                self.link_source = self.link_source.split("?", 1)[0]

            if self.link_source.find("/") != -1 and self.extension != "md":
                name = self.link_source.split("/")[-1]
            else:
                name = self.link_source

            self.filename = self._clean(name)  # cleanly normalized name but extension still part of it
            # e.g. balance_inspiration_motivation_life_scene_wander_big.jpg
            if self.filename.strip() == "":
                return self.error("filename is empty")

            # only possible for images (video, image)
            if self.source.startswith("!"):
                self.cat = "image"
                if not self.extension in ["png", "jpg", "jpeg", "mov", "mp4", "svg"]:
                    return self.error("found unsupported image file: extension:%s" % self.extension)

            if self.cat == "":
                if self.extension in ["png", "jpg", "jpeg", "mov", "mp4"]:
                    self.cat = "imagelink"
                elif self.extension in ["doc", "docx", "pdf", "xls", "xlsx", "pdf"]:
                    self.cat = "officedoc"
                elif self.extension in ["md", "", None]:
                    self.cat = "doc"  # link to a markdown document
                    try:
                        self.link_to_doc = self.docsite.doc_get(self.link_source, die=False)
                    except Exception as e:
                        if "Cannot find doc" in str(e):
                            return self.error(str(e))
                        raise e
                else:
                    # j.shell()
                    return self.error("found unsupported extension")

            if self.extension == "md":
                doc = self.doc.docsite.doc_get(self.filename, die=False)
                if doc:
                    self.filepath = doc.path
            else:
                self.filepath = self.doc.docsite.file_get(self.filename, die=False)

    @property
    def markdown(self):
        if self.source.startswith("!"):
            c = "!"
            if self.link_source_original is not "":
                descr = "%s@%s" % (self.link_descr, self.link_source_original)
            else:
                descr = self.link_descr
        else:
            c = ""
            descr = self.link_descr
        c += "[%s](%s)" % (descr, self.link_source)
        return c

    def download(self, dest):
        if not "http" in self.link_source:
            return
        self._log_info("download:%s\n%s" % (self.link_source_original, dest))
        ddir = j.sal.fs.getDirName(dest)
        if not j.sal.fs.exists(dest):
            import requests

            response = requests.get(self.link_source_original, stream=True)
            j.sal.fs.writeFile(dest, response.content, append=False)

    def should_skip(self):
        return any(link in self.link_source for link in SKIPPED_LINKS) or j.data.types.email.check(self.link_source)

    def link_verify(self):
        def do():
            if self.should_skip():
                return True
            self._log_info("check link exists:%s" % self.link_source)
            if not j.clients.http.ping(self.link_source_original):
                self.error("link not alive:%s" % self.link_source_original)
                return False
            return True

        res = self._cache.get(self.link_source, method=do, expire=3600)
        if res is not True:
            self.error(res)
            return False

    def replace_in_txt(self, txt):
        if len(self.source) < 4:
            j.shell()
            raise j.exceptions.Base("something wrong with original source")
        txt = txt.replace(self.source, self.markdown)
        # self.source = self.markdown #there is a new source now
        return txt

    def __repr__(self):
        if self.cat == "link":
            return "link:%s:%s" % (self.cat, self.link_source)
        else:
            return "link:%s:%s" % (self.cat, self.filename)

    __str__ = __repr__
