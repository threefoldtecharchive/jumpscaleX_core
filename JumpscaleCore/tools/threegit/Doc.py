import toml
import copy
import re
import traceback

from urllib.parse import urlparse, parse_qs, parse_qsl
from .Link import Link

from jinja2 import Environment, FileSystemLoader, select_autoescape
from Jumpscale import j

JSBASE = j.baseclasses.object

# for macro templates
templates_path = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), "macros", "templates")
env = Environment(loader=FileSystemLoader(templates_path), autoescape=select_autoescape(["html", "xml"]))


class Doc(j.baseclasses.object):
    """
    """

    def __init__(self, path, name, docsite, sonic_client=None):
        JSBASE.__init__(self)
        self.path = path
        self.docsite = docsite
        self.sonic_client = sonic_client

        self.cat = ""
        if "/blogs/" in path or "/blog/" in path:
            self.cat = "blog"
        if "/defs/" in path or "/def/" in path:
            self.cat = "def"

        self.path_dir = j.sal.fs.getDirName(self.path)
        self.path_dir_rel = j.sal.fs.pathRemoveDirPart(self.path_dir, self.docsite.path).strip("/")
        self.name = self._clean(name)
        if self.name == "":
            raise j.exceptions.Base("name cannot be empty")
        self.name_original = name
        self.path_rel = j.sal.fs.pathRemoveDirPart(path, self.docsite.path).strip("/")

        name_dot = "%s/%s" % (self.path_dir_rel, self.name)
        self.name_dot_lower = self._clean("%s/%s" % (self.path_dir_rel, self.name))

        self.errors = []

        self._processed = False

        self._extension = None

        self._data = {}  # is all data, from parents as well, also from default data

        self._md = None

        self._content = None

        self._links = []
        self.render_obj = None
        if self.sonic_client:
            self.register_sonic()

    def render_macro_template(self, name, **kwargs):
        return env.get_template(name).render(**kwargs)

    def chunks(self, txt, length):
        for i in range(0, len(txt), length):
            if i + length > len(txt):
                yield txt[i:]
            else:
                yield txt[i : i + length]

    def register_sonic(self):
        text = self.markdown_source.replace("\n", " ").strip()
        if not text:
            return
        if " " in self.name:
            print("file {} can't be indexed it contains space in the file name")
            return
        for chunck in self.chunks(text, int(self.sonic_client.bufsize) // 2):
            try:
                self.sonic_client.push("docsites", self.docsite.name, self.path_rel, chunck)
            except Exception as e:
                print("Couldn't index {}".format(self.name))

    def _clean(self, name):
        name = name.replace("/", ".")
        name = name.strip(".")
        return j.core.text.convert_to_snake_case(name)

    @property
    def links(self):
        if self._links == []:
            self._links_process()
        return self._links

    @property
    def images(self):
        return self.links_get(cat="image")

    @property
    def extension(self):
        if not self._extension:
            self._extension = j.sal.fs.getFileExtension(self.path)
        return self._extension

    @property
    def title(self):
        if "title" in self.data:
            return self.data["title"]
        else:
            self.error_raise("Could not find title in doc.")

    def error_raise(self, msg):
        return self.docsite.error_raise(msg, doc=self)

    @property
    def data(self):
        if self._data == {}:

            # look for parts which are data
            for part in self.parts_get(cat="data"):
                for key, val in part.ddict.items():
                    print("data update")
                    if j.data.types.list.check(val):
                        if key not in self._data:
                            self._data[key] = []
                        for subval in val:
                            if subval not in self._data[key] and subval != "":
                                self._data[key].append(subval)
                    else:
                        self._data[key] = val

            # now we have all data from the document itself

            keys = [part for part in self.docsite.data_default.keys()]
            keys.sort(key=len)
            for key in keys:
                key = key.strip("/")
                if self.path_rel.startswith(key):
                    data = self.docsite.data_default[key]
                    self._data_update(data)
            print("data process doc")

        return self._data

    @property
    def markdown_obj(self):
        if not self._md:
            self._md = j.data.markdown.document_get(self.markdown_source)
        return self._md

    def header_get(self, level=1, nr=0):
        res = self.markdown_obj.parts_get(cat="header")
        if len(res) < 1:
            return self.error_raise("header level:%s %s could not be found" % (level, nr))
        for header in res:
            if header.level == level:
                return header

    def _process(self):
        if not self._processed:
            self._macros_process()
            self._links_process()
            self._processed = True

    @property
    def markdown(self):
        """
        markdown after processing of the full doc
        """
        self._process()
        res = self.markdown_obj.markdown

        if "{{" in res:
            # TODO:*1 rendering does not seem to be ok
            res = j.tools.jinja2.template_render(text=res, obj=self.render_obj, **self.data)
        return res

    @property
    def markdown_source(self):
        """
        markdown coming from source
        """
        if not self._content:
            self._content = j.sal.fs.readFile(self.path)
        return self._content

    @property
    def markdown_clean(self):
        # remove the code blocks (comments are already gone)
        print("markdown_clean")
        from IPython import embed

        embed(colors="Linux")
        return None

    @property
    def markdown_clean_summary(self):
        c = self.markdown_source
        lines = c.split("\n")
        counter = 0
        out = ""
        while counter < 20 and counter < len(lines):
            line = lines[counter]
            counter += 1
            if line.strip() == "" and counter > 10:
                return out
            if len(line) > 0 and line.strip()[0] == "#" and counter > 4:
                return out
            out += "%s\n" % line
        return out

    def _data_update(self, data):
        res = {}
        for key, valUpdate2 in data.items():
            # check for the keys not in the self.data yet and add them, the others are done above
            if key not in self._data:
                self._data[key] = copy.copy(valUpdate2)  # needs to be copy.copy otherwise we rewrite source later

    def link_get(self, filename=None, cat=None, nr=0, die=True):
        """
        @param cat: image, doc,link, officedoc, imagelink  #doc is markdown
        """
        res = self.links_get(filename=filename, cat=cat)
        if len(res) == 0:
            if die:
                raise j.exceptions.Base("could not find link %s:%s" % (filename, cat))
            else:
                return None
        if nr > len(res):
            if die:
                raise j.exceptions.Base("could not find link %s:%s at position:%s" % (filename, cat, nr))
            else:
                return None
        return res[nr]

    def links_get(self, filename=None, cat=None):
        """
        @param cat: image, doc,link, officedoc, imagelink  #doc is markdown
        :param filename:
        :return:
        """
        self._links_process()
        res = []
        for link in self._links:
            found = True
            if cat is not None and not link.cat == cat:
                found = False
            if filename is not None and not link.filename.startswith(filename):
                found = False
            if found:
                res.append(link)
        return res

    def _args_get(self, methodcode):
        if "(" in methodcode:
            methodcode = methodcode.split("(", 1)[1]
            methodcode = methodcode.rstrip(", )")  # remove end )
            args = [
                item.strip().strip('"').strip("'").strip() for item in methodcode.split(",") if item.find("=") == -1
            ]
        else:
            args = []
        return args

    def _kwargs_get(self, methodcode):
        if "(" in methodcode:
            methodcode = methodcode.split("(", 1)[1]
            methodcode = methodcode.rstrip(", )")  # remove end )
        kwargs_ = [item.strip() for item in methodcode.split(",") if item.find("=") != -1]
        if kwargs_ != []:
            kw = {}
            for item in kwargs_:
                pre, post = item.split("=", 1)
                kw[pre.strip()] = eval(post)
            return kw
        else:
            return {}

    def _macros_process(self):
        """
        eval the macros
        """

        if not self.docsite.threegit:
            return

        for part in self.parts_get(cat="macro"):
            if part.method.strip() == "":
                return self.docsite.error_raise("empty macro cannot be executed", doc=self)

            macro_name = part.method.split("(", 1)[0].strip()

            if not macro_name in self.docsite.threegit._macros:
                e = "COULD NOT FIND MACRO"
                block = "```python\nERROR IN MACRO*** TODO: *1 ***\nmacro:\n%s\nERROR:\n%s\n```\n" % (macro_name, e)
                self._log_error(block)
                self.docsite.error_raise(block, doc=self)

            method = self.docsite.threegit._macros[macro_name]
            args = self._args_get(part.method)
            kwargs = self._kwargs_get(part.method)
            if j.data.types.dict.check(part.data):
                kwargs.update(part.data)

            # part.result = method(self,*args,**kwargs,content=part.data)
            try:
                part.result = method(self, *args, **kwargs)
            except Exception as e:
                if hasattr(e, "message"):
                    e = e.message
                block = "```python\nERROR IN MACRO*** TODO: *1 ***\nmacro:\n%s\nERROR:\n%s\n%s```\n" % (
                    macro_name,
                    e,
                    traceback.format_exc(),
                )
                self._log_error(block)
                self.docsite.error_raise(block, doc=self)
                part.result = block

    def _links_process(self):
        """
        results in:
            self._links with Link objects
        """
        if not self._links == []:
            return
        if self.markdown_source == "":
            return
        regex = Link.LINK_MARKDOWN_PATTERN
        for match in j.data.regex.yieldRegexMatches(regex, self.markdown_source, flags=re.X):
            self._log_debug("##:file:link:%s" % match)
            link = Link(self, match.founditem)
            if not link.link_source == "" and not self._link_exists(link):
                self._links.append(link)

    def part_get(self, text_to_find=None, cat=None, nr=0, die=True):
        """
        return part of markdown document e.g. header

        @param cat is: table, header, macro, code, comment1line, comment, block, data, image
        @param nr is the one you need to have 0 = first one which matches
        @param text_to_find looks into the text
        """
        return self.markdown_obj.part_get(text_to_find=text_to_find, cat=cat, nr=nr, die=die)

    def parts_get(self, text_to_find=None, cat=None):
        """
        @param cat is: table, header, macro, code, comment1line, comment, block, data, image
        @param text_to_find looks into the text
        """
        return self.markdown_obj.parts_get(text_to_find=text_to_find, cat=cat)

    def write(self):
        self._log_info("write:%s" % self)
        md = self.markdown  # just to trigger the error checking
        j.sal.fs.createDir(j.sal.fs.joinPaths(self.docsite.outpath, self.path_dir_rel))
        for link in self._links:
            if link.filename:
                dest_file = j.sal.fs.joinPaths(self.docsite.outpath, self.path_dir_rel, link.filename)

                if link.filepath and not j.sal.fs.exists(dest_file):
                    # make sure parent dir of dest_file exists
                    j.sal.fs.createDir(j.sal.fs.getParent(dest_file))
                    j.sal.fs.copyFile(link.filepath, dest_file)
                else:
                    if link.source.startswith("!"):
                        link.download(dest=dest_file)
                # now change the right link in the doc
                # link.link_source = j.sal.fs.pathRemoveDirPart(dest_file,self.docsite.outpath)
                # Set link source to the file name only as it gets its files from current page path
                link.link_source = link.filename
            md = link.replace_in_txt(md)

        dest = j.sal.fs.joinPaths(self.docsite.outpath, self.path_dir_rel, self.name) + ".md"

        j.sal.fs.writeFile(dest, md, append=False)

    def _link_exists(self, link):
        for l in self._links:
            if l.link_source == link.link_source:
                return True
        return False

    def link_add(self, link_src, path=None):
        l = Link(self, link_src)
        if not self._link_exists(l):
            self._links.append(l)

    def __repr__(self):
        return "doc:%s:%s" % (self.name, self.path)

    __str__ = __repr__
