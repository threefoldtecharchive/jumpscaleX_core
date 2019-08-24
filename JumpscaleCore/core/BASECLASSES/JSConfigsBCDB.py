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


class JSConfigsBCDB(JSConfigBCDBBase):
    def _childclass_selector(self, jsxobject, **kwargs):
        """
        allow custom implementation of which child class to use
        :return:
        """
        return self.__class__._CHILDCLASS

    def new(self, name, jsxobject=None, save=True, **kwargs):
        """
        it it exists will delete if first when delete == True
        :param name:
        :param jsxobject:
        :param save:
        :param kwargs:
        :return:
        """
        if self.exists(name=name):
            raise j.exceptions.Base("cannot do new object, exists")
        return self._new(name=name, jsxobject=jsxobject, save=save, **kwargs)

    def _new(self, name, jsxobject=None, save=True, **kwargs):
        """
        :param name: for the CONFIG item (is a unique name for the service, client, ...)
        :param jsxobject: you can right away specify the jsxobject
        :param kwargs: the data elements which will be given to JSXObject underneith (given to constructor)
        :return: the service
        """
        if not jsxobject:
            jsxobject = self._model.new(data=kwargs)
            jsxobject.name = name

        # means we need to remember the parent id
        if isinstance(self._parent, j.baseclasses.object_config):
            if not self._parent._id:
                self._parent.save()
                assert self._parent._id
            jsxobject.parent_id = self._parent._id

        jsconfig_klass = self._childclass_selector(jsxobject=jsxobject)
        jsconfig = jsconfig_klass(parent=self, jsxobject=jsxobject)
        jsconfig._triggers_call(jsconfig, "new")
        self._children[name] = jsconfig
        if save:
            self._children[name].save()
            self._children[name]._autosave = True
        return self._children[name]

    def get(self, name="main", needexist=False, save=True, **kwargs):
        """
        :param name: of the object
        """

        jsconfig = self._get(name=name, die=needexist)

        if not jsconfig:
            self._log_debug("NEW OBJ:%s:%s" % (name, self._name))
            jsconfig = self._new(name=name, save=save, **kwargs)
        else:
            # check that the stored values correspond with kwargs given
            changed = False
            for key, val in kwargs.items():
                if not getattr(jsconfig, key) == val:
                    changed = True
                    setattr(jsconfig, key, val)
            if changed and save:
                jsconfig.save()

        jsconfig._triggers_call(jsconfig, "get")
        return jsconfig

    def _get(self, name="main", die=True):
        assert name
        if name in self._children:
            return self._children[name]

        self._log_debug("get child:'%s'from '%s'" % (name, self._name))

        # new = False
        res = self.find(name=name)

        if len(res) < 1:
            if not die:
                return
            raise j.exceptions.Base(
                "Did not find instance for:%s, name searched for:%s" % (self.__class__._location, name)
            )

        elif len(res) > 1:
            raise j.exceptions.Base(
                "Found more than 1 service for :%s, name searched for:%s" % (self.__class__._location, name)
            )
        else:
            jsxconfig = res[0]

        return jsxconfig

    def reset(self):
        """
        will destroy all data in the DB, be carefull
        :return:
        """
        self._log_debug("reset all data")
        for item in self.find():
            item.delete()
        self._children = j.baseclasses.dict()

    def find(self, **kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the config objects
        """
        res = []
        for key, item in self._children.items():
            match = True
            for key, val in kwargs.items():
                if hasattr(item, key):
                    if val != getattr(item, key):
                        match = False
                else:
                    raise j.exceptions.Value("could not find for prop:%s, did not exist in %s" % (key, self._key))
            if match:
                res.append(item)

        for jsxobject in self._findData(**kwargs):
            name = jsxobject.name
            if not name in self._children:
                r = self._new(name=name, jsxobject=jsxobject)
                res.append(r)
        return res

    def count(self, **kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the config objects
        """
        return len(self._findData(**kwargs))

    def _findData(self, **kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the data objects (the data of the model)
        """

        if isinstance(self._parent, j.baseclasses.object_config):
            if not self._parent._id:
                self._parent.save()
                assert self._parent._id
            kwargs["parent_id"] = str(self._parent._id)

        if len(kwargs) > 0:
            propnames = [i for i in kwargs.keys()]
            propnames_keys_in_schema = [
                item.name for item in self._model.schema.properties_index_keys if item.name in propnames
            ]
            if len(propnames_keys_in_schema) > 0:
                # we can try to find this config
                return self._model.find(**kwargs)
            else:
                raise j.exceptions.Base(
                    "cannot find obj with kwargs:\n%s\n in %s\nbecause kwargs do not match, is there * in schema"
                    % (kwargs, self)
                )
            return []
        else:
            return self._model.find()

    def delete(self, name):
        self._model
        if name in self._children:
            self._children.pop(name)
        res = self._findData(name=name)
        if len(res) == 0:
            return
        elif len(res) == 1:
            self._model.delete(res[0].id)

    def exists(self, name="main"):
        """
        :param name: of the object
        """
        if name in self._children:
            return True
        res = self._findData(name=name)
        if len(res) > 1:
            raise j.exceptions.Base(
                "found too many items for :%s, name:\n%s\n%s" % (self.__class__.__name__, name, res)
            )
        elif len(res) == 1:
            return True
        else:
            return False
