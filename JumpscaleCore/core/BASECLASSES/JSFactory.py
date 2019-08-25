from .JSBase import JSBase
from Jumpscale import j
from .Attr import Attr
from .TestTools import TestTools
from .JSConfigBCDB import JSConfigBCDB


class JSFactory(JSBase):
    def _init_pre_factory(self, **kwargs):

        # these are classes which will be created automatically when the factory class starts
        if hasattr(self.__class__, "_CHILDCLASSES"):
            for kl in self.__class__._CHILDCLASSES:
                # childclasses are the e.g. JSConfigs classes

                if not kl._name:
                    raise j.exceptions.JSBug("Cannot start childclass it has no _name")
                    # name = j.core.text.strip_to_ascii_dense(str(kl)).split(".")[-1].lower()
                else:
                    name = kl._name
                assert name

                obj = kl(parent=self, **kwargs)
                assert obj._parent
                self._children[name] = obj

        if hasattr(self.__class__, "_CHILDFACTORY_CLASS"):
            # there is only a new function if there is a childclass factory
            self.new = self._new

        self._object_config_factory = None
        self._object_config = None

    def _init_post(self, **kwargs):

        if not self._object_config and self._object_config_factory:
            # means we can create the default object
            assert "name" in kwargs
            name = kwargs["name"]
            self._object_config = self._object_config_factory.new(name=name)

        if self._object_config:
            assert self._object_config._name
            assert isinstance(self._object_config, JSConfigBCDB)

    def _childclass_selector(self, **kwargs):
        return self.__class__._CHILDFACTORY_CLASS

    def _obj_cache_reset(self):
        """
        make sure that all objects we remember inside are emptied
        :return:
        """
        JSBase._obj_cache_reset(self)
        for factory in self._children.values():
            factory._obj_cache_reset()

        if self._object_config:
            self._object_config._obj_cache_reset()

    def reset(self):
        """
        careful is a very dangerous function, will delete all children (call reset and delete on each child)
        if there is a config object attached to it, it will also delete it

        :return:
        """
        for item in self._children.items():
            if hasattr(item, "reset"):
                item.reset()

        self.delete()

    def save(self):
        for item in self._children_recursive_get():
            if hasattr(item, "save"):
                item.save()

        if self._object_config:
            self._object_config.save()

    def _dataprops_names_get(self, filter=None):
        # means there is an object attached to it
        if self._object_config:
            self._object_config._dataprops_names_get()
        return []

    def _children_names_get(self, filter=None):
        """
        :param filter: is '' then will show all, if None will ignore _
                when * at end it will be considered a prefix
                when * at start it will be considered a end of line filter (endswith)
                when R as first char its considered to be a regex
                everything else is a full match

        :param self:
        :param filter:
        :return:
        """

        def do():
            x = []
            for key, item in self._children.items():
                x.append(key)
            return x

        x = self._cache.get(key="_children_names_get", method=do, expire=10)  # will redo every 10 sec
        return self._filter(filter=filter, llist=x, nameonly=True)

    def _children_get(self, filter=None):
        """
        :param filter: is '' then will show all, if None will ignore _
                when * at end it will be considered a prefix
                when * at start it will be considered a end of line filter (endswith)
                when R as first char its considered to be a regex
                everything else is a full match

        :return:
        """
        x = []
        for key, item in self._children.items():
            x.append(item)
        return self._filter(filter=filter, llist=x, nameonly=False)

    def _new(self, name, save=False, **kwargs):
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
        return self._new2(name=name, save=save, **kwargs)

    def _new2(self, name, save=False, **kwargs):
        """
        :param name: for the CONFIG item (is a unique name for the service, client, ...)
        :return: the service
        """
        klass = self._childclass_selector(**kwargs)
        child = klass(parent=self, **kwargs)
        assert child._name
        assert child._parent
        self._children[name] = child
        if save:
            self._children[child].save()
        return self._children[name]

    def get(self, name="main", needexist=False, save=False, **kwargs):
        """

        :param name: of the child to get, if it doesn't need to exist then will try to create new
        new one can only be created if self.__class__._CHILDFACTORY_CLASS has been set


        """
        if not name in self._children:
            if hasattr(self.__class__, "_CHILDFACTORY_CLASS") and needexist == False:
                self.new(name=name, save=save, **kwargs)
            else:
                raise j.exceptions.Value("cannot get child with name:%s" % name)
        return self._children[name]

    def find(self, **kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the children objects found
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
        return res

    def count(self, name, recursive=False):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the config objects
        """
        r = 0
        if name in self._children:
            child = self._children[name]
            if hasattr(child, "count"):
                r += child.count(name=name)

    def delete(self, name=None, recursive=False):
        if name in self._children:
            if recursive:
                self._children[name].delete(name=name, recursive=recursive)
            self._children.pop(name)

        if self._object_config:
            self._object_config.reset()

    def exists(self, name="main"):
        """
        :param name: of the object
        """
        if name in self._children:
            return True


class JSFactoryProtected(JSFactory, Attr):
    pass


class JSFactoryTesttools(JSFactory, TestTools):
    pass


class JSFactoryProtectedTesttools(JSFactory, TestTools, Attr):
    pass
