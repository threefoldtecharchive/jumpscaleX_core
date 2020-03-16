from Jumpscale import j
from .TypeBaseClass import TypeBaseClass


class TypeBaseObjClassFactory(TypeBaseClass):

    __NAME = None
    __ALIAS = None  # list if more than 1
    __DEFAULT = None
    __SUBOBJECT_CLASS = TypeBaseObjClass

    def check(self, value):
        if isinstance(value, TypeBaseObjClass):
            return True

    def fromString(self, txt):
        return self.clean(txt)

    def toJSON(self, v):
        return self.toString(v)

    def toString(self, val):
        val = self.clean(val)
        return val._string

    def python_code_get(self, value):
        """
        produce the python code which represents this value
        """
        val = self.clean(value)
        return val._python_code

    def toData(self, v):
        v = self.clean(v)
        return v.toData()
        # raise j.exceptions.NotImplemented()

    def clean(self, v, parent=None):
        raise j.exceptions.NotImplemented()


class TypeBaseObjClass:
    """
    is a custom type object (so not the factory/class who instancianated this obj)
    it has the data inside !
    """

    __slots__ = ["__changed", "__data", "__serialized"]

    __NAME = None
    __ALIAS = None  # list if more than 1
    __FACTORY_CLASS = TypeBaseObjClassFactory
    __SERIALIZED__ = False

    def __init__(self, typebase, value=None):
        self.__changed = False
        self.__data = value
        # to know if the serialized data is stored, or the direct usable one
        self.__serialized = self.__class.__SERIALIZED__  # can be overruled at instance time

    @property
    def _changed(self):
        return self.__changed

    @_changed.setter
    def _changed(self, value):
        assert value == False  # only supported mode
        self.__changed = False

    @property
    def _string(self):
        raise j.exceptions.NotImplemented()

    @property
    def _python_code(self):
        raise j.exceptions.NotImplemented()

    @property
    def _data(self):
        return self.__data

    @property
    def _value(self):
        if self.__serialized:
            return self._typebase.clean(self.__data)
        return self.__data

    @value.setter
    def _value(self, val):
        d = self._typebase.toData(val)
        if self.__data != d:
            self.__data = d
            self.__changed = True

    def __str__(self):
        if self.__data:
            return "%s: %s" % (self._typebase.__class__.NAME, self._string)
        else:
            return "%s: NOTSET" % (self._typebase.__class__.NAME)

    __repr__ = __str__
