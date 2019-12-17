import sys

from Jumpscale import j
from .Schema import Schema
from .SchemaMeta import SchemaMeta
from .JSXObject import JSXObject


class SchemaFactory(j.baseclasses.factory_testtools):
    __jslocation__ = "j.data.schema"

    def _init(self, **kwargs):

        self.__code_generation_dir = None
        self.meta = SchemaMeta()
        self._reset_state()
        self._JSXObjectClass = JSXObject
        self.models_in_use = False  # if this is set then will not allow certain actions to happen here
        self._schemas = None

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
        self.schemas_url = j.baseclasses.dict(name="SCHEMASURL")  # is url to schema
        self._schemas = None

    @property
    def schemas(self):
        if not self._schemas:
            self._schemas = j.baseclasses.dict(name="SCHEMAS")
            for url in self.meta.schema_urls:
                if url in self.schemas_url:
                    self._schemas[url] = self.schemas_url[url]
                else:
                    self.get(url=url)
        return self._schemas

    def exists(self, md5=None, url=None):
        if md5:
            if md5 in self.schemas_md5:
                return True
        elif url:
            if url in self.schemas_url:
                return True
        return self.meta.exists(md5=None, url=None)

    def schema_cache_remove(self, url):
        if url in self._schemas:
            self._schemas.pop(url)
        if url in self.schemas_url:
            s = self.schemas_url[url]
            self.schemas_url.pop(url)
            if s._md5 in self.schemas_md5:
                self.schemas_md5.pop(s._md5)

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
            self.get_from_text(data["text"])
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
        if not die:
            if not self.exists(url=url):
                return None
        url = self._urlclean(url)
        # if not in mem yet will load here
        if url not in self.schemas_url:
            if not self.meta.exists(url=url):
                raise j.exceptions.Input("Could not find schema with url:%s" % url)
            data = self.meta.schema_get(url=url)
            self.get_from_text(data["text"], url=data["url"])
            # return self.schemas_url[data["url"]]
        if not url in self.schemas_url:
            raise j.exceptions.Base("url schould be same as data[url]")
            # j.debug()
            # s = self.get_from_text(data["text"], url=url)
            # j.shell()
            # w
        return self.schemas_url[url]

    def is_multiple_schema_from_text(self, schema_text):
        """
        will return true if the schema text conatins more than one schema

        Returns:
            bool
        """
        assert isinstance(schema_text, str)
        blocks = self._schema_blocks_get(schema_text)
        return len(blocks) > 1

    def get_from_text(self, schema_text, url=None, skipfirst=False, multiple=False):
        """
        will return the first schema specified if more than 1

        Returns:
            Schema
        """
        assert isinstance(schema_text, str)
        self._check_bcdb_is_not_used()
        res = []
        blocks = self._schema_blocks_get(schema_text)
        if len(blocks) > 1 and url:
            raise j.exceptions.Input("cannot support add from text with url if more than 1 block")
        for i, block in enumerate(blocks):
            if i == 0 and skipfirst:
                continue
            res.append(self._get_from_text_single(block, url=url))
        if not multiple:
            if len(res) > 0:
                return res[0]
        else:
            return res

    def _get_from_text_single(self, schema_text, url=None):
        """
        can only be 1 schema

        Returns:
            Schema
        """
        assert isinstance(schema_text, str)

        md5 = self._md5(schema_text)
        if md5 in self.schemas_md5:
            s = self.schemas_md5[md5]
            self.set_schema(s)
            return s

        s = Schema(text=schema_text, md5=md5, url=url)

        self.set_schema(s)

        return s

    def set_schema(self, schema):
        self.schemas_url[schema.url] = schema
        self.schemas_md5[schema._md5] = schema
        self.schemas[schema.url] = schema
        self.meta.schema_set(schema)

    def _md5(self, text):
        """
        convert text to md5 in reproduceable way
        """
        assert len(self._schema_blocks_get(text)) == 1  # need to be removed later TODO:
        original_text = text.replace(" ", "").replace("\n", "").strip()
        # print("*****\n%s\n***********\n"%(ascii_text))
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
        self._test_run(name=name)
