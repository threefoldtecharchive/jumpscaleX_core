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


from Jumpscale import j

JSBASE = j.baseclasses.object


class SchemaProperty(j.baseclasses.object):
    def _init(self, **kwargs):

        self.name = ""
        self.jumpscaletype = None
        self.comment = ""
        self.nr = 0
        self._default = None
        self.index = False  # as used in sqlite
        self.index_key = False  # is for indexing the keys
        self.index_text = False  # is for full text index
        self.unique = False  # to check if type is unique or not
        if self.name in ["schema"]:
            raise j.exceptions.Base("cannot have property name:%s" % self.name)

    @property
    def capnp_schema(self):
        return self.jumpscaletype.capnp_schema_get(self.name_camel, self.nr)

    @property
    def default(self):
        if self._default:
            return self._default
        return self.jumpscaletype.default_get()

    @property
    def has_jsxobject(self):
        return self.is_list_jsxobject or self.is_jsxobject

    @property
    def is_list_jsxobject(self):
        if self.jumpscaletype.NAME == "list" and self.jumpscaletype.SUBTYPE.NAME == "JSXOBJ":
            return True
        return False

    @property
    def is_jsxobject(self):
        if self.jumpscaletype.BASETYPE == "JSXOBJ":
            return True
        return False

    @property
    def is_list(self):
        if self.jumpscaletype.NAME == "list":
            return True
        return False

    @property
    def default_as_python_code(self):
        c = self.jumpscaletype.python_code_get(self.default)
        # try:
        #     c = self.jumpscaletype.python_code_get(self.default)
        # except Exception as e:
        #     raise j.exceptions.JSBUG("cannot get pythoncode from default", exception=e)
        return c

    @property
    def name_camel(self):
        out = ""
        for item in self.name.split("_"):
            if out is "":
                out = item.lower()
            else:
                out += item.capitalize()
        return out

    @property
    def name_str(self):
        return "%-20s" % self.name

    @property
    def js_typelocation(self):
        return self.jumpscaletype._jsx_location

    def __str__(self):
        if not self.jumpscaletype.NAME == "list":
            out = "prop:%-25s %s" % (self.name, self.jumpscaletype.NAME)
        else:
            out = "prop:%-25s %s" % (self.name, self.jumpscaletype)

        # if self.pointer_type:
        #     out += " !%s" % self.pointer_type
        return out

    __repr__ = __str__
