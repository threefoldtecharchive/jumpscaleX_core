from Jumpscale import j
from .JSConfigBCDBBase import JSConfigBCDBBase


class JSConfigsBCDB(JSConfigBCDBBase):
    def _childclass_selector(self, jsxobject, **kwargs):
        """
        allow custom implementation of which child class to use
        :return:
        """
        return self.__class__._CHILDCLASS

    def new(self, name, jsxobject=None, autosave=True, **kwargs):
        """
        it it exists will delete if first when delete is True
        :param name:
        :param jsxobject:
        :param autosave: sets the autosave argument on the data and also saves the object before the function returns. If set to False, you need to explicitly save the object.
        :param kwargs:
        :return:
        """
        if not name:
            raise j.exceptions.Input("name needs to be specified on a config mgmt obj")
        if self.exists(name=name):
            raise j.exceptions.Base(f"cannot do new object, {name} exists")
        jsconfig = self._create(name=name, jsxobject=jsxobject, autosave=autosave, **kwargs)
        self._check(jsconfig)
        return jsconfig

    def _check_children(self):
        if not self._cache_use:
            assert self._children == j.baseclasses.dict()

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

    def _create(self, name, jsxobject=None, autosave=None, **kwargs):
        """
        :param name: for the CONFIG item (is a unique name for the service, client, ...)
        :param jsxobject: you can right away specify the jsxobject
        :param kwargs: the data elements which will be given to JSXObject underneith (given to constructor)
        :return: the service
        """
        if jsxobject:
            if not name:
                name = jsxobject.name
            else:
                assert name == jsxobject.name
        if not name:
            raise j.exceptions.Input("name needs to be specified on a config mgmt obj")

        def process_kwargs(kwargs):
            kwargs_to_class = {}
            if kwargs:
                kwargs_to_obj_new = {}
                props = [i.name for i in self._model.schema.properties]
                for key, val in kwargs.items():
                    if key in props:
                        kwargs_to_obj_new[key] = val
                    else:
                        kwargs_to_class[key] = val
            else:
                kwargs_to_obj_new = {}
                kwargs_to_class = {}
            return kwargs_to_obj_new, kwargs_to_class

        kwargs_to_obj_new, kwargs_to_class = process_kwargs(kwargs)

        if not jsxobject:
            if kwargs_to_obj_new:
                jsxobject = self._model.new(data=kwargs_to_obj_new)
            else:
                jsxobject = self._model.new()
            jsxobject.name = name

        # means we need to remember the parent id
        mother_id = self._mother_id_get()
        if mother_id:
            if jsxobject.mother_id != mother_id:
                jsxobject.mother_id = mother_id

        jsconfig_klass = self._childclass_selector(jsxobject=jsxobject)
        jsconfig = jsconfig_klass(parent=self, jsxobject=jsxobject, **kwargs_to_class)
        self._children[name] = jsconfig

        if autosave != None:
            jsxobject._autosave = autosave

        if jsxobject._autosave:
            self._children[name].save()

        return self._children[name]

    def get(self, name="main", id=None, needexist=False, autosave=True, reload=False, **kwargs):
        """
        :param name: of the object
        """
        name = name.replace("__", ".")
        if not name:
            raise j.exceptions.Input("name needs to be specified on a config mgmt obj")

        # will reload if needed (not in self._children)
        rc, jsconfig = self._get(name=name, id=id, die=needexist, reload=reload)

        if not jsconfig:
            self._log_debug("NEW OBJ:%s:%s" % (name, self._classname))
            jsconfig = self._create(name=name, autosave=autosave, **kwargs)
        else:
            # check that the stored values correspond with kwargs given
            # means comes from the database
            if not jsconfig._data._model.schema._md5 == jsconfig._model.schema._md5:
                # means data came from DB and schema is not same as config mgmt class
                # j.shell()
                j.debug()
                raise j.exceptions.Input(
                    "models should be same", data=(jsconfig._data._model.schema.text, jsconfig._model.schema.text)
                )
            changed = False
            jsconfig._data._autosave = False
            props = [i.name for i in self._model.schema.properties]
            for key, val in kwargs.items():
                if key not in props:
                    raise j.exceptions.Input(
                        "cannot set property:'%s' on obj because not part of the schema" % key, data=jsconfig
                    )
                if not getattr(jsconfig, key) == val:
                    changed = True
                    setattr(jsconfig, key, val)
            if changed and autosave:
                jsconfig.save()

            jsconfig._autosave = autosave

        # lets do some tests (maybe in future can be removed, but for now the safe bet)
        self._check(jsconfig)

        return jsconfig

    def _get(self, name="main", id=None, die=True, reload=False, autosave=None):
        """

        :param name:
        :param id: id will always have priority
        :param die: if False will return None if it cannot be found
        :param reload: if exists, will ask the data to be reloaded
        :param autosave:
        :return: 1,obj or 2,obj
            2 if exists
            1 if new
        """

        if id:
            obj = self._model.get(id)
            name = obj.name
            return 1, self._create(name, obj, autosave=autosave)

        obj = self._validate_child(name)
        if obj:
            if reload:
                obj.load()
            return 1, obj

        # self._log_debug("get child:'%s'from '%s'" % (name, self._classname))

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

        if autosave != None:
            jsxconfig._autosave = autosave

        return 2, jsxconfig

    def reset(self):
        """
        will destroy all data in the DB, be carefull
        :return:
        """
        self._log_debug("reset all data")
        # delete the all children of the factory
        for item in self._children_names_get():
            self.delete(item)

        for id in self._model.find_ids():
            self._model.delete(id)

        assert self._model.index.sql_index_count() == 0
        if not self._mother_id_get():
            self._model.index.destroy()
        self._children = j.baseclasses.dict()

    def _children_names_get(self, filter=None):
        condition = False
        Item = self._model.index.sql
        mother_id = self._mother_id_get()

        if mother_id:
            condition = Item.mother_id == mother_id
        if filter and filter != "*":
            condition = Item.name.startswith(filter) and condition if condition else Item.name.startswith(filter)

        if condition:
            res = [i.name for i in Item.select().where(condition) if self._model.exists(i.id)]
        else:
            res = [i.name for i in Item.select() if self._model.exists(i.id)]

        # every item returned here NEEDS to actually exist on the model.
        # FIXME: future update
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
        for key, item in list(self._children.items()):
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
                item = self.get(id=id, reload=reload, autosave=False)
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

    def delete(self, name=None):
        """
        :param name:
        :return:
        """
        self._delete(name=name)

    def _delete(self, name=None):
        if name:
            _, child = self._get(name=name, die=False)
            if child:
                return child.delete()
        else:
            return self.reset()

        if not name and self._parent:
            if self._classname in self._parent._children:
                if not isinstance(self._parent, j.baseclasses.factory):
                    # only delete when not a factory means is a custom class we're building
                    del self._parent._children[self._data.name]

    def exists(self, name="main"):
        """
        :param name: of the object
        """
        obj = self._validate_child(name)
        if obj:
            return True

        # will only use the index
        r = self.count(name=name)
        if r == 1:
            return True
        if r == 0:
            return False
        raise j.exceptions.Base("should never be more than 1 result")

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
        for _, item in self._children.items():
            x.append(item)
        x = self._filter(filter=filter, llist=x, nameonly=False)
        # be smarter in how we use the index
        for item in self.find():
            if item not in x:
                x.append(item)
        return x

    def __str__(self):
        return "jsxconfigobj:collection:%s" % self._model.schema.url
