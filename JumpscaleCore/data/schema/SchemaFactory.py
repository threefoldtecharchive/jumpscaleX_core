import sys

from Jumpscale import j
from .Schema import Schema
from .SchemaMeta import SchemaMeta
from .JSXObjectSub import JSXObjectSub
from .JSXObjectRoot import JSXObjectRoot
from .JSXObjectBase import JSXObjectBase

TESTTOOLS = j.baseclasses.testtools


class SchemaFactory(j.baseclasses.factory_testtools, TESTTOOLS):
    __jslocation__ = "j.data.schema"

    def _init(self, **kwargs):

        self.__code_generation_dir = None
        self.meta = SchemaMeta()
        self._reset_state()
        self._JSXObjectClassRoot = JSXObjectRoot
        self._JSXObjectClassSub = JSXObjectSub
        self._JSXObjectClass = JSXObjectBase
        self.models_in_use = False  # if this is set then will not allow certain actions to happen here

    @property
    def SCHEMA_CLASS(self):
        return Schema

    @property
    def _code_generation_dir(self):
        if not self.__code_generation_dir:
            path = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "schema")
            j.sal.fs.createDir(path)
            if path not in sys.path:
                sys.path.append(path)
            j.sal.fs.touch(j.sal.fs.joinPaths(path, "__init__.py"))
            self._log_debug("codegendir:%s" % path)
            self.__code_generation_dir = path
        return self.__code_generation_dir

    def _reset_state(self):
        """
        be very careful because this will probably make your install corrupt, schema's will not be found
        :return:
        """
        self.schemas_md5 = j.baseclasses.dict(name="SCHEMASMD5")  # is md5 to schema
        self.schemas_loaded = j.baseclasses.dict(name="SCHEMASURL")  # is url to schema

    def reset(self):
        self.meta.reset()
        self._reset_state()

    @property
    def schemas_all(self):
        for url in self.meta.schema_urls:
            if url not in self.schemas_loaded:
                self.get(url=url)
        return self.schemas_loaded

    def exists(self, md5=None, url=None):
        if md5:
            if md5 in self.schemas_md5:
                return True
        elif url:
            if url in self.schemas_loaded:
                return True
        return self.meta.exists(md5=md5, url=url)

    def schema_cache_remove(self, url):
        if url in self.schemas_loaded:
            s = self.schemas_loaded[url]
            self.schemas_loaded.pop(url)
            if s._md5 in self.schemas_md5:
                self.schemas_md5.pop(s._md5)
            self.meta._data["url"].pop(url, None)
            self.meta._data["md5"].pop(s._md5, None)

    def get(self, md5=None, url=None, text=""):
        """
        get the schema, caching happens
        :param md5:
        :param url:
        :return:
        """
        if md5:
            return self.get_from_md5(md5=md5)
        if text:
            return self.get_from_text(text, url=url)
        elif url:
            return self.get_from_url(url=url)
        else:
            raise j.exceptions.Input("need to specify md5 or url")

    def get_from_md5(self, md5):
        """
        :param md5: each schema has a unique md5 which is its identification string
        :return: Schema
        """
        assert isinstance(md5, str)
        if not md5 in self.schemas_md5:
            data = self.meta.schema_get(md5=md5)
            s = self.get_from_text(data["text"], newest=False)  # important we don't fetch the newest
            if md5 not in self.schemas_md5:
                self.schemas_md5[md5] = s
        return self.schemas_md5[md5]

    def _urlclean(self, url):
        assert isinstance(url, str)
        url = url.lower()
        url = url.strip()
        return url

    def get_from_url(self, url, die=True):
        """
        :param url: url is e.g. jumpscale.bcdb.user.1
        :return: will return the most recent schema, there can be more than 1 schema with same url (changed over time)
        """
        # shortcut for performance
        if url in self.schemas_loaded:
            return self.schemas_loaded[url]
        if not die:
            if not self.exists(url=url):
                return None
        url = self._urlclean(url)
        # if not in mem yet will load here
        if url not in self.schemas_loaded:
            if not self.meta.exists(url=url):
                raise j.exceptions.Input("Could not find schema with url:%s" % url)
            data = self.meta.schema_get(url=url)
            self.get_from_text(data["text"], url=data["url"])
            # return self.schemas_loaded[data["url"]]
        if not url in self.schemas_loaded:
            raise j.exceptions.Base("url schould be same as data[url]")
            # j.debug()
            # s = self.get_from_text(data["text"], url=url)
            # j.shell()
            # w
        return self.schemas_loaded[url]

    def is_multiple_schema_from_text(self, schema_text):
        """
        will return true if the schema text conatins more than one schema

        Returns:
            bool
        """
        assert isinstance(schema_text, str)
        blocks = self._schema_blocks_get(schema_text)
        return len(blocks) > 1

    def get_from_text(self, schema_text, url=None, newest=True, save=True):
        """
        will return the first schema specified if more than 1

        @param newest when set will replace the metadata even if it exists & the caching
        @param save , means will be remembered in metadata config

        Returns:
            Schema
        """
        assert isinstance(schema_text, str)
        self._check_bcdb_is_not_used()
        res = []
        blocks = self._schema_blocks_get(schema_text)
        for i, block in enumerate(blocks):
            if i == 0:
                # first one can take url
                res.append(self._get_from_text_single(block, url=url, newest=newest, save=save))
            else:
                # 2nd one needs to have url specified
                res.append(self._get_from_text_single(block, newest=newest, save=save))

            # keep track of all inner schemas (root, and sub schema meta)
            for block in blocks:
                url_line = block.splitlines()[0]
                schema_url = url
                if "@url" in url_line:
                    schema_url = url_line.split("=")[1].strip()
                if not self.exists(url=schema_url):
                    rewritten = self._schema_text_rewrite(schema_url, block)
                    md5 = self._md5(rewritten, blocktest=False)
                    s = Schema(text=rewritten, url=schema_url, md5=md5)
                    j.data.schema.meta.schema_set(s)

        if len(res) > 0:
            return res[0]

    def _schema_text_rewrite(self, url=None, schema_text=None):
        """
        will add url to schema_text if not there yet
        :param url:
        :param schema_text:
        :return:
        """
        assert schema_text
        schema_text = j.core.tools.text_strip(schema_text)
        found_nrs = False
        nr = 0
        out = ""

        def remove_comment(line):
            if "#" not in line:
                return line
            line1, line2 = line.split("#", 1)
            return line1.strip()

        for line in schema_text.split("\n"):
            line = line.strip()
            line = line.replace("::", ":")  # there was some but at one point of time
            if line.startswith("@url"):
                if url:
                    continue
                else:
                    url = line.split("=", 1)[1].strip()
                    continue
            if line.startswith("@"):
                out += "%s\n" % line
            elif line.strip() == "":
                continue
            elif line.strip().startswith("#"):
                continue
            elif ":" in line[0:4]:
                found_nrs = True
                out += "%s\n" % remove_comment(line)
            else:
                if found_nrs:
                    raise j.exceptions.Input("cannot mix nr's and no nrs in schema", data=[url, schema_text])
                assert ":" not in line[0:3]
                out += "%-2s: %s\n" % (nr, remove_comment(line))
                nr += 1
        schema_text = out
        assert url
        assert len(url) > 5
        schema_text = "@url = %s\n%s\n" % (url, schema_text.strip())
        return schema_text

    def _get_from_text_single(self, schema_text, url=None, newest=False, save=True):
        """
        can only be 1 schema

        Returns:
            Schema
        """
        assert isinstance(schema_text, str)

        schema_text = self._schema_text_rewrite(url, schema_text)
        md5 = self._md5(schema_text, rewrite=False)

        if md5 in self.schemas_md5:
            s = self.schemas_md5[md5]
            if url:
                assert s.url == url
        else:
            s = Schema(text=schema_text, url=url, md5=md5)

        if save:
            j.data.schema.meta.schema_set(s, newest=newest)
            if newest or s.url not in j.data.schema.schemas_loaded:
                j.data.schema.schemas_loaded[s.url] = s
            if newest or s._md5 not in j.data.schema.schemas_md5:
                j.data.schema.schemas_md5[s._md5] = s
        return s

    def _md5(self, text, blocktest=True, rewrite=True):
        """
        convert text to md5 in reproduceable way
        """
        if blocktest:
            r = self._schema_blocks_get(text)
            assert len(r) == 1
            text = r[0]
        if rewrite:
            text = self._schema_text_rewrite(schema_text=text)
        original_text = text.replace(" ", "").replace("\n", "").strip()
        return j.data.hash.md5_string(original_text)

    def _schema_blocks_get(self, schema_text):
        """
        cut schematext into multiple blocks
        :param schema_text:
        :return:
        """
        block = ""
        blocks = []
        txt = j.core.text.strip(schema_text)
        for line in txt.split("\n"):

            strip_line = line.lower().strip()

            if block == "":
                if strip_line == "" or strip_line.startswith("#"):
                    continue

            if strip_line.startswith("@url"):
                if block is not "":
                    blocks.append(block)
                    block = ""

            block += "%s\n" % line

        # process last block
        if block is not "":
            blocks.append(block)

        return blocks

    def _check_bcdb_is_not_used(self):
        return
        if self.models_in_use:
            raise j.exceptions.JSBUG("should not modify schema's when models used through this interface")

    def add_from_path(self, path=None):
        """
        :param path, is path where there are .toml schema's which will be loaded

        will not load model files, only toml !

        """
        res = []
        # if j.sal.fs
        if j.sal.fs.isFile(path):
            paths = [path]
        else:
            paths = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.toml", followSymlinks=True)
        for schemapath in paths:
            bname = j.sal.fs.getBaseName(schemapath)[:-5]
            if bname.startswith("_"):
                continue

            schema_text = j.sal.fs.readFile(schemapath)

            schema = self.get_from_text(schema_text=schema_text)
            if schema not in res:
                res.append(schema)
        return res

    def test(self, name=""):
        """
        it's run all tests
        kosmos 'j.data.schema.test()'
        kosmos 'j.data.schema.test(name="base")'

        if want run specific test ( write the name of test ) e.g. j.data.schema.test(name="base")
        """
        self._tests_run(name=name, die=True)
