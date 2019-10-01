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
from .JSConfigBCDBBase import JSConfigBCDBBase

"""
classes who use JSXObject for data storage but provide nice interface to enduser
"""


class JSConfigBCDB(JSConfigBCDBBase):
    def _init_pre2(self, jsxobject=None, datadict=None, name=None, **kwargs):

        if jsxobject:
            self._data = jsxobject
        else:
            jsxobjects = []
            if name:
                jsxobjects = self._model.find(name=name)
            if len(jsxobjects) > 0:
                self._data = jsxobjects[0]
            else:
                self._data = self._model.new()  # create an empty object

        if datadict:
            assert isinstance(datadict, dict) or isinstance(datadict, j.baseclasses.dict)
            self._data_update(datadict)

        if name and self._data.name != name:
            self._data.name = name

    @property
    def _autosave(self):
        return self._data._autosave

    @_autosave.setter
    def _autosave(self, val):
        self._data._autosave = val

    @property
    def name(self):
        return self._data.name

    @property
    def _key(self):
        assert self.name
        return self._classname + "_" + self.name

    @property
    def _name(self):
        assert self._classname
        return self._classname

    @property
    def _id(self):
        return self._data.id

    @property
    def id(self):
        return self._data.id

    def _data_update(self, datadict):
        """
        will not automatically save the data, don't forget to call self.save()

        :param kwargs:
        :return:
        """
        # ddict = self._data._ddict  # why was this needed? (kristof)
        self._data._data_update(datadict=datadict)

    def delete(self):
        """
        :return:
        """
        self._delete()

    def load(self):
        """
        load from bcdb
        :return:
        """
        jsxobjects = self._model.find(name=self.name)
        if len(jsxobjects) == 0:
            raise j.exceptions.JSBUG("cannot find obj:%s for reload" % self.name)
        self._data = jsxobjects[0]
        self._data._autosave = True
        return self

    def _delete(self):
        self._triggers_call(self, "delete")
        assert self._model
        self._model.delete(self._data)
        if self._parent:
            if self._data.name in self._parent._children:
                if not isinstance(self._parent, j.baseclasses.factory):
                    # if factory then cannot delete from the mother because its the only object
                    del self._parent._children[self._data.name]

        self._children_delete()

        self._triggers_call(self, "delete_post")

    def save(self):
        self.save_()

    def save_(self):
        assert self._model
        self._triggers_call(self, "save")

        mother_id = self._mother_id_get()
        if mother_id:
            # means there is a mother
            self._data.mother_id = mother_id
            assert self._data._model.schema._md5 == self._model.schema._md5

        self._data.save()

        self._triggers_call(self, "save_post")

    def edit(self):
        """

        edit data of object in editor
        chosen editor in env var: "EDITOR" will be used

        :return:

        """
        path = j.core.tools.text_replace("{DIR_TEMP}/js_baseconfig_%s.toml" % self.__class__._location)
        data_in = self._data._toml
        j.sal.fs.writeFile(path, data_in)
        j.core.tools.file_edit(path)
        data_out = j.sal.fs.readFile(path)
        if data_in != data_out:
            self._log_debug(
                "'%s' instance '%s' has been edited (changed)" % (self._parent.__jslocation__, self._data.name)
            )
            data2 = j.data.serializers.toml.loads(data_out)
            self._data.data_update(data2)
        j.sal.fs.remove(path)

    def _dataprops_names_get(self, filter=None):
        """
        e.g. in a JSConfig object would be the names of properties of the jsxobject = data
        e.g. in a JSXObject would be the names of the properties of the data itself

        :return: list of the names
        """
        return self._filter(filter=filter, llist=self._model.schema.propertynames)

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        out = "{BLUE}# JSXOBJ:{RESET}\n"
        print(j.core.tools.text_replace(out, die_if_args_left=False).rstrip())
        return self._data.__repr__()
        #
        # out = "{YELLOW}## JSXOBJ: %s{RESET}\n\n" % (self.__class__._classname,)
        #
        # def add(name, color, items, out):
        #     if len(items) > 0:
        #         out += "{GREEN} - ID: %s\n{%s}" % (self._id, color)
        #         if len(items) < 20:
        #             for item in items:
        #                 self._log_debug(item)
        #                 item = item.rstrip()
        #                 if name in ["data", "properties"]:
        #                     try:
        #                         v = j.core._data_serializer_safe(getattr(self, item)).rstrip()
        #                         if "\n" in v:
        #                             # v = j.core.tools.text_indent(content=v, nspaces=4)
        #                             v = "\n".join(v.split("\n")[:1])
        #                             out += " - %-20s : {GRAY}%s{%s}\n" % (item, v, color)
        #                         else:
        #                             out += " - %-20s : {GRAY}%s{%s}\n" % (item, v, color)
        #
        #                     except Exception as e:
        #                         out += " - %-20s : {GRAY}ERROR ATTRIBUTE{%s}\n" % (item, color)
        #                 else:
        #                     out += " - %s\n" % item
        #         else:
        #             out += " - ...\n"
        #     out += "\n"
        #     return out
        #
        # out = add("data", "BLUE", self._dataprops_names_get(), out)
        #
        # out += "{RESET}"
        #
        # out = j.core.tools.text_replace(out, die_if_args_left=False)
        # print(out)
        #
        # # TODO: *1 dirty hack, the ansi codes are not printed, need to check why
        # return ""
