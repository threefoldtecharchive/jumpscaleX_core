# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


import sys

from .Schema import Schema
from Jumpscale import j
from .JSXObject import JSXObject


class SchemaFactory(j.baseclasses.factory_testtools):
    __jslocation__ = "j.data.schema"

    def _init(self, **kwargs):

        self.__code_generation_dir = None
        self.reset()
        self._JSXObjectClass = JSXObject
        self.models_in_use = False  # if this is set then will not allow certain actions to happen here
        self.schemas = j.baseclasses.dict(name="SCHEMAS")
        self.schemas_md5 = j.baseclasses.dict(prefix="MD5_", name="SCHEMA2MD5")

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

    def reset(self):
        self._url_to_md5 = j.baseclasses.dict()
        self._md5_to_schema = j.baseclasses.dict()

    def exists(self, md5=None, url=None):
        if md5:
            return md5 in self._md5_to_schema
        elif url:
            return url in self._url_to_md5

    def get_from_md5(self, md5):
        """
        :param md5: each schema has a unique md5 which is its identification string
        :return: Schema
        """
        assert isinstance(md5, str)
        if md5 in self._md5_to_schema:
            schema_text_or_obj = self._md5_to_schema[md5]
            if isinstance(schema_text_or_obj, str):
                if schema_text_or_obj.strip() == "":
                    raise j.exceptions.JSBUG("schema should never be empty string")
                md5, schema = self._add_text_to_schema_obj(schema_text_or_obj)
            assert isinstance(self._md5_to_schema[md5], j.data.schema.SCHEMA_CLASS)
            return self._md5_to_schema[md5]
        else:
            raise j.exceptions.Input("Could not find schema with md5:%s" % md5)

    def get_from_url(self, url, die=True):
        """
        :param url: url is e.g. jumpscale.bcdb.user.1
        :return: will return the most recent schema, there can be more than 1 schema with same url (changed over time)
        """
        assert isinstance(url, str)
        url = self._urlclean(url)
        if url in self._url_to_md5:
            s = self.get_from_md5(self._url_to_md5[url])
            self.schemas._add(s.url, s)
            return s
        if die:
            raise j.exceptions.Input("Could not find schema with url:%s" % url)

    def is_multiple_schema_from_text(self, schema_text):
        """
        will return true if the schema text conatins more than one schema

        Returns:
            bool
        """
        assert isinstance(schema_text, str)
        blocks = self._schema_blocks_get(schema_text)
        return len(blocks) > 1

    def get_from_text(self, schema_text, url=None, multiple=False):
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
        for block in blocks:
            res.append(self._get_from_text_single(block, url=url))
        if multiple:
            return res
        return res[0]

    def get_from_text_single(self, schema_text):
        res = self.get_from_text(schema_text, multiple=True)
        if res == 0 or res > 1:
            raise j.exceptions.JSBUG("can only add 1 schema in text", data=schema_text)
        return res[0]

    def _get_from_text_single(self, schema_text, url=None):
        """
        can only be 1 schema

        Returns:
            Schema
        """
        assert isinstance(schema_text, str)
        md5, schema = self._add_text_to_schema_obj(schema_text=schema_text, url=url)
        return self.get_from_md5(md5)

    def _md5(self, text):
        """
        convert text to md5
        """
        assert len(self._schema_blocks_get(text)) == 1  # need to be removed later TODO:
        original_text = text.replace(" ", "").replace("\n", "").strip()
        # print("*****\n%s\n***********\n"%(ascii_text))
        return j.data.hash.md5_string(original_text)

    def _urlclean(self, url):
        """
        url = j.data.schema._urlclean(url)
        :param url:
        :return:
        """
        return url.strip().strip("'\"").strip()

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

    def _add_text_to_schema_obj(self, schema_text, url=None):
        """
        add the text to our structure and convert to schema object
        :param schema_text:
        :param url:
        :return:
        """
        md5 = self._md5(schema_text)
        if md5 in self._md5_to_schema and not isinstance(self._md5_to_schema[md5], str):
            return md5, self._md5_to_schema[md5]

        s = Schema(text=schema_text, md5=md5, url=url)

        # here we always update the md5 because if we are here it means
        # that we have added a new schema
        self._url_to_md5[s.url] = md5

        self._md5_to_schema._add(md5, s)
        self.schemas_md5._add(md5, s)

        self.schemas._add(s.url, s)

        assert s.url

        return md5, s

    def add_from_path(self, path=None):
        """
        :param path, is path where there are .toml schema's which will be loaded

        will not load model files, only toml !

        """
        self._check_bcdb_is_not_used()
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
            # toml_path = "%s.toml" % (schema.key)
            # if j.sal.fs.getBaseName(schemapath) != toml_path:
            #     toml_path = "%s/%s.toml" % (j.sal.fs.getDirName(schemapath), schema.key)
            #     j.sal.fs.renameFile(schemapath, toml_path)
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
