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
        jsconfig = self._new(name=name, jsxobject=jsxobject, save=save, **kwargs)
        self._check(jsconfig)
        return jsconfig

    def _check_children(self):
        if not self._cache_use:
            assert self._children == {}

    def _check(self, jsconfig):
        if jsconfig._id is None:
            # model has never been saved no check required yet
            return

        # lets do some tests (maybe in future can be removed, but for now the safe bet)
        assert jsconfig._id > 0
        mother_id = jsconfig._mother_id_get()
        if mother_id:
            assert jsconfig.mother_id == mother_id
        assert jsconfig._model.schema._md5 == self._model.schema._md5

    def _new(self, name, jsxobject=None, save=True, **kwargs):
        """
        :param name: for the CONFIG item (is a unique name for the service, client, ...)
        :param jsxobject: you can right away specify the jsxobject
        :param kwargs: the data elements which will be given to JSXObject underneith (given to constructor)
        :return: the service
        """
        kwargs_to_class = {}
        if not jsxobject:
            if kwargs:
                kwargs_to_obj_new = {}
                props = [i.name for i in self._model.schema.properties]
                for key, val in kwargs.items():
                    if key in props:
                        kwargs_to_obj_new[key] = val
                    else:
                        kwargs_to_class[key] = val
                jsxobject = self._model.new(data=kwargs_to_obj_new)
            else:
                jsxobject = self._model.new()
            jsxobject.name = name

        jsxobject._autosave = True

        # means we need to remember the parent id
        mother_id = self._mother_id_get()
        if mother_id:
            if jsxobject.mother_id != mother_id:
                jsxobject.mother_id = mother_id
                jsxobject.save()

        jsconfig_klass = self._childclass_selector(jsxobject=jsxobject)
        jsconfig = jsconfig_klass(parent=self, jsxobject=jsxobject, **kwargs_to_class)
        jsconfig._triggers_call(jsconfig, "new")
        jsconfig._autosave = True
        self._children[name] = jsconfig
        if save:
            self._children[name].save()

        return self._children[name]

    def get(self, name="main", id=None, needexist=False, save=True, reload=False, **kwargs):
        """
        :param name: of the object
        """

        # will reload if needed (not in self._children)
        rc, jsconfig = self._get(name=name, id=id, die=needexist, reload=reload)

        if not jsconfig:
            self._log_debug("NEW OBJ:%s:%s" % (name, self._classname))
            jsconfig = self._new(name=name, save=save, **kwargs)
        else:
            # check that the stored values correspond with kwargs given
            # means comes from the database
            if not jsconfig._data._model.schema._md5 == jsconfig._model.schema._md5:
                # means data came from DB and schema is not same as config mgmt class
                j.shell()
            changed = False
            jsconfig._data._autosave = False
            for key, val in kwargs.items():
                if not getattr(jsconfig, key) == val:
                    changed = True
                    setattr(jsconfig, key, val)
            if changed and save:
                jsconfig.save()

        # lets do some tests (maybe in future can be removed, but for now the safe bet)
        self._check(jsconfig)

        jsconfig._triggers_call(jsconfig, "get")

        jsconfig._autosave = True

        return jsconfig

    def _get(self, name="main", id=None, die=True, reload=False):

        if id:
            obj = self._model.get(id)
            name = obj.name
            self._children[name] = obj
            return 1, self._new(name, obj)

        if name in self._children:
            if reload:
                self._children[name].load()
            return 1, self._children[name]

        self._log_debug("get child:'%s'from '%s'" % (name, self._classname))

        # new = False
        res = self.find(name=name)

        if len(res) < 1:
            if not die:
                return 3, None
            raise j.exceptions.Base(
                "Did not find instance for:%s, name searched for:%s" % (self.__class__._location, name)
            )

        elif len(res) > 1:
            raise j.exceptions.Base(
                "Found more than 1 service for :%s, name searched for:%s" % (self.__class__._location, name)
            )
        else:
            jsxconfig = res[0]

        jsxconfig._autosave = True

        return 2, jsxconfig

    def reset(self, recursive=None):
        """
        will destroy all data in the DB, be carefull
        :return:
        """
        self._log_debug("reset all data")
        for item in self.find():
            try:
                item.delete()
            except Exception as e:
                j.shell()

        mother_id = self._mother_id_get()
        # TODO: in fact this should work without having to do this, we put it in to get to some more tests, but if deletes work well it should work without (JO)
        if not mother_id:
            # means we can remove all objects of the url (index)
            self._model.index.destroy()
        else:
            # if we did not specify and there is a mother_id for sure we can do the recursive behaviour
            if recursive == None:
                recursive = True

        if recursive:
            self._children_delete(recursive=recursive)

        self._children = j.baseclasses.dict()

    def _children_names_get(self, filter=None):
        Item = self._model.index.sql
        if filter:
            res = [i.name for i in Item.select().where(Item.name.startswith(filter))]
        else:
            res = [i.name for i in Item.select()]

        if len(res) > 50:
            return []

        return res

    def find(self, reload=False, **kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the config objects
        """

        res = []
        ids_done = []
        for key, item in self._children.items():
            match = True
            for key, val in kwargs.items():
                if item._hasattr(key):
                    if val != getattr(item, key):
                        match = False
                else:
                    match = False
            if match:
                if reload:
                    item.load()
                res.append(item)
                if item.id not in ids_done:
                    ids_done.append(item.id)

        kwargs = self._kwargs_update(kwargs)

        # this is more efficient no need to go to backend stor if the objects are already in mem
        ids = self._model.find_ids(**kwargs)
        for id in ids:
            if id not in ids_done:
                item = self.get(id=id, reload=reload, save=False)
                res.append(item)

        return res

    def _kwargs_update(self, kwargs):
        mother_id = self._mother_id_get()
        if mother_id:
            kwargs["mother_id"] = mother_id
        return kwargs

    def count(self, **kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the config objects
        """
        kwargs = self._kwargs_update(kwargs)
        # TODO do proper count query
        return len(list(self._model.find_ids(**kwargs)))

    def _findData(self, **kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the data objects (the data of the model)
        """

        kwargs = self._kwargs_update(kwargs)
        return self._model.find(**kwargs)

    def save(self):
        for item in self._children_get():
            if item._hasattr("save"):
                item.save()

    def delete(self, name=None, recursive=None):
        """

        :param name:
        :param recursive: None means will be True if there is a mother, otherwise will be False or True forced
        :return:
        """
        self._delete(name=name, recursive=recursive)

    def _delete(self, name=None, recursive=None):
        self._model
        if recursive == None and self._mother_id_get():
            recursive = True
        if name:
            res = self._findData(name=name)
            if len(res) == 0:
                return
            elif len(res) == 1:
                self._model.delete(res[0].id)
        else:
            return self.reset(recursive=recursive)

        if name in self._children:
            if recursive:
                self._children[name].delete(recursive=recursive)
            self._children.pop(name)

        if not name and self._parent:
            if self._classname in self._parent._children:
                if not isinstance(self._parent, j.baseclasses.factory):
                    # only delete when not a factory means is a custom class we're building
                    del self._parent._children[self._data.name]

    def exists(self, name="main"):
        """
        :param name: of the object
        """
        if name in self._children:
            return True
        # will only use the index
        return self.count(name=name) == 1

    def _children_get(self, filter=None):
        """
        :param filter: is '' then will show all, if None will ignore _
                when * at end it will be considered a prefix
                when * at start it will be considered a end of line filter (endswith)
                when R as first char its considered to be a regex
                everything else is a full match
        :return:
        """
        # TODO implement filter properly
        x = []
        for key, item in self._children.items():
            x.append(item)
        x = self._filter(filter=filter, llist=x, nameonly=False)
        # be smarter in how we use the index
        for item in self.find():
            if item not in x:
                x.append(item)
        return x

    def __str__(self):
        return "jsxconfigobj:collection:%s" % self._model.schema.url
