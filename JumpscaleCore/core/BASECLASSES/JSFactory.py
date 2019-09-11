from Jumpscale import j

from .Attr import Attr
from .JSBase import JSBase


from .TestTools import TestTools

# from .JSConfigBCDB import JSConfigBCDB


class JSFactory(JSBase, Attr):
    def _init_factory(self, **kwargs):

        # these are classes which will be created automatically when the factory class starts
        if hasattr(self.__class__, "_CHILDCLASSES"):
            for kl in self.__class__._CHILDCLASSES:
                # childclasses are the e.g. JSConfigs classes

                # if not kl._name or not isinstance(kl._name, str):
                #     name = j.core.text.strip_to_ascii_dense(str(kl)).split(".")[-1].lower()
                # else:
                obj = kl(parent=self, **kwargs)
                name = obj._name
                assert obj._parent
                self._children[name] = obj

    def _children_names_get(self, filter=None):
        r = [str(i) for i in self._children.keys()]
        return self._filter(filter=filter, llist=r)

    def _childclass_selector(self, **kwargs):
        return self.__class__._CHILDCLASS

    def _obj_cache_reset(self):
        """
        make sure that all objects we remember inside are emptied
        :return:
        """
        JSBase._obj_cache_reset(self)
        for factory in self._children.values():
            factory._obj_cache_reset()

        # if self._object_config:
        #     self._object_config._obj_cache_reset()

    def reset(self):
        """
        careful is a very dangerous function, will delete all children (call reset and delete on each child)
        if there is a config object attached to it, it will also delete it

        :return:
        """
        self.delete()

    def save(self):
        for item in self._children_get():
            if isinstance(item, j.baseclasses.object):
                if item._hasattr("save"):
                    item.save()
            else:
                raise j.exceptions.JSBUG("only suport j.baseclasses.object")

        # if self._object_config:
        #     self._object_config.save()

    # def _dataprops_names_get(self, filter=None):
    #     # means there is an object attached to it
    #     if self._object_config:
    #         self._object_config._dataprops_names_get()
    #     return []

    # def _children_names_get(self, filter=None):
    #     """
    #     :param filter: is '' then will show all, if None will ignore _
    #             when * at end it will be considered a prefix
    #             when * at start it will be considered a end of line filter (endswith)
    #             when R as first char its considered to be a regex
    #             everything else is a full match
    #
    #     :param self:
    #     :param filter:
    #     :return:
    #     """
    #
    #     def do():
    #         x = []
    #         for key, item in self._children.items():
    #             x.append(key)
    #         return x
    #
    #     x = self._cache.get(key="_children_names_get", method=do, expire=10)  # will redo every 10 sec
    #     return self._filter(filter=filter, llist=x, nameonly=True)

    # def _children_get(self, filter=None):
    #     """
    #     :param filter: is '' then will show all, if None will ignore _
    #             when * at end it will be considered a prefix
    #             when * at start it will be considered a end of line filter (endswith)
    #             when R as first char its considered to be a regex
    #             everything else is a full match
    #
    #     :return:
    #     """
    #     x = []
    #     for key, item in self._children.items():
    #         x.append(item)
    #     return self._filter(filter=filter, llist=x, nameonly=False)

    # def _new(self, name, save=False, **kwargs):
    #     """
    #     it it exists will delete if first when delete == True
    #     :param name:
    #     :param jsxobject:
    #     :param save:
    #     :param kwargs:
    #     :return:
    #     """
    #     if self.exists(name=name):
    #         raise j.exceptions.Base("cannot do new object, exists")
    #     return self._new2(name=name, save=save, **kwargs)
    #
    # def _new2(self, name, save=False, **kwargs):
    #     """
    #     :param name: for the CONFIG item (is a unique name for the service, client, ...)
    #     :return: the service
    #     """
    #     klass = self._childclass_selector(**kwargs)
    #     child = klass(parent=self, **kwargs)
    #     assert child._name
    #     assert child._parent
    #     self._children[name] = child
    #     if save:
    #         self._children[child].save()
    #     return self._children[name]

    def get(self, name="main", needexist=False, save=False, reload=False, **kwargs):
        """

        :param name: of the child to get, if it doesn't need to exist then will try to create new
        new one can only be created if self.__class__._CHILDCLASS has been set


        """
        if not name in self._children:
            if hasattr(self.__class__, "_CHILDCLASS") and needexist == False:
                self.new(name=name, save=save, **kwargs)
            else:
                raise j.exceptions.Value("cannot get child with name:%s" % name)
        if reload:
            self._children[name].load()
        return self._children[name]

    def find(self, **kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the children objects found
        """
        res = []
        for key, item in self._children.items():
            match = True
            if isinstance(item, j.baseclasses.object_config):
                for key, val in kwargs.items():
                    print("need to check in properties of schema to see if we can check")
                    j.shell()
            elif isinstance(item, j.baseclasses.object):
                for key, val in kwargs.items():
                    if item._hasattr(key):
                        if val != getattr(item, key):
                            match = False
                    else:
                        raise j.exceptions.Value("could not find for prop:%s, did not exist in %s" % (key, self._key))
            else:
                raise j.exceptions.JSBUG("only support jsx objects in _children")
            if match:
                res.append(item)
        return res

    # def count(self, name):
    #     """
    #     :param kwargs: e.g. color="red",...
    #     :return: list of the config objects
    #     """
    #     raise j.exceptions.NotImplemented()
    #     # r = 0
    #     # if name in self._children:
    #     #     child = self._children[name]
    #     #     if self._hasattr(child, "count"):
    #     #         r += child.count(name=name)

    def delete(self, name=None, recursive=None):
        """

        :param name:
        :param recursive: None means will be True if there is a mother, otherwise will be False or True forced
        :return:
        """
        self._delete(name=name, recursive=recursive)

    def _delete(self, name=None, recursive=None):

        if recursive == None and self._mother_id_get():
            recursive = True

        if name:
            if name in self._children:
                if recursive:
                    self._children[name].delete(recursive=recursive)
                self._children.pop(name)

        self._children_delete(recursive=recursive)

        if self._parent:
            # if we exist in the parent remove us from their children
            if self._classname in self._parent._children:
                self._parent._children.pop(self._classname)

    def exists(self, name="main"):
        """
        :param name: of the object
        """
        if name in self._children:
            return True
