from Jumpscale import j
from .TypeBaseClass import TypeBaseClass


class TypeBaseObjClassFactory(TypeBaseClass):

    __name = ""
    __object_class = TypeBaseObjClass

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
    is a custom type object (so not the factory/class who instancianted this obj)
    it hsa the data inside !
    """

    __slots__ = ["__changed", "__data", "__serialized"]
    __default = None
    __serialized__ = True

    def __init__(self, typebase, value=None):
        self.__changed = False
        self.__data = value
        # to know id the serialized data is stored, or the direct usable one
        self.__serialized = self.__class.__serialized__  # can be overruled at instance time

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
    def value(self):
        if self.__serialized:
            return self._typebase.clean(self.__data)
        return self.__data

    @value.setter
    def value(self, val):
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


class TypeBaseObjClassNumeric(TypeBaseObjClass):

    BASETYPE = "OBJ"

    @property
    def value(self):
        raise j.exceptions.NotImplemented()

    # def __eq__(self, other):
    #     n = self._typebase.clean(other)
    #     return self.value == n.value

    def __gt__(self, other):
        n = self._typebase.clean(other)
        return self.value > n.value

    def __ge__(self, other):
        n = self._typebase.clean(other)
        return self.value >= n.value

    def __lt__(self, other):
        n = self._typebase.clean(other)
        return self.value < n.value

    def __le__(self, other):
        n = self._typebase.clean(other)
        return self.value <= n.value

    # def __add__(self, other):
    #     n = self._typebase.clean(other)
    #     r = self.value + n.value
    #     return self._typebase.clean(r)
    #
    # def __sub__(self, other):
    #     n = self._typebase.clean(other)
    #     r = self.value - n.value
    #     return self._typebase.clean(r)
    #
    # def __mul__(self, other):
    #     n = self._typebase.clean(other)
    #     r = self.value * n.value
    #     return self._typebase.clean(r)
    #
    # def __div__(self, other):
    #     n = self._typebase.clean(other)
    #     r = self.value / n.value
    #     return self._typebase.clean(r)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        other = self._typebase.clean(other)
        return float(other) == float(self)

    def __bool__(self):
        return self._data is not None

    def _other_convert(self, other):
        return self._typebase.clean(other)

    def __add__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(other) + float(self))

    def __iadd__(self, other):
        other = self._other_convert(other)
        self.value = float(self) + float(other)
        return self

    def __sub__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) - float(other))

    def __mul__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) * float(other))

    def __matmul__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) @ float(other))

    def __truediv__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) / float(other))

    def __floordiv__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) // float(other))

    def __mod__(self, other):
        raise NotImplemented()

    def __divmod__(self, other):
        raise NotImplemented()

    def __pow__(self, other):
        raise NotImplemented()

    def __lshift__(self):
        raise NotImplemented()

    def __neg__(self):
        return self._typebase.clean(float(self) * -1)

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    __rshift__ = __lshift__
    __and__ = __lshift__
    __xor__ = __lshift__
    __or__ = __lshift__
