from Jumpscale import j


class TypeBaseObjClass:

    BASETYPE = "OBJ"
    __slots__ = ["_typebase", "_value"]

    def __init__(self, typebase, value=None):

        self._typebase = typebase  # is the factory for this object

        if value is None:
            self._data = 0
        else:
            self._data = self._data_from_init_val(value)

    def _data_from_init_val(self, value):
        """
        convert init value to raw type inside this object
        :return:
        """
        return value

    def _capnp_schema_get(self, name, nr):
        return self._typebase.capnp_schema_get(name, nr)

    @property
    def _string(self):
        raise j.exceptions.NotImplemented()

    @property
    def _python_code(self):
        raise j.exceptions.NotImplemented()

    @property
    def _datadict(self):
        return self._data

    @property
    def value(self):
        raise j.exceptions.NotImplemented()

    def default_get():
        return None

    @value.setter
    def value(self, val):
        self._data = self._typebase.toData(val)

    def __str__(self):
        if self._data:
            return "%s: %s" % (self._typebase.__class__.NAME, self._string)
        else:
            return "%s: NOTSET" % (self._typebase.__class__.NAME)

    __repr__ = __str__


class TypeBaseObjClassNumeric(TypeBaseObjClass):

    BASETYPE = "OBJ"

    @property
    def value(self):
        raise j.exceptions.NotImplemented()

    # def __hash__(self):
    #     return hash(self.value)

    def __eq__(self, other):
        # other = self._other_convert(other)
        # if other is None:
        #     j.shell()
        #     raise j.exceptions.Value("cannot compare with None")
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


class TypeBaseClass:  #!!TYPEBASECLASS!!

    # CUSTOM = False #if custom will create new instance depending specification in default

    def __init__(self):
        self.BASETYPE = None
        self.ALIAS = None
        self.NAME = None
        self._default = None

    def toString(self, v):
        return str(self.clean(v))

    def toHR(self, v):
        return self.toString(v)

    def toDict(self, v):
        raise NotImplemented()

    def toDictHR(self, v):
        raise NotImplemented()

    def toData(self, v):
        """
        first clean then get the data for capnp
        :param v:
        :return:
        """
        o = self.clean(v)
        if isinstance(o, TypeBaseObjClass):
            data = o._datadict
        else:
            data = o
        return data

    def check(self, value):
        """
        - if there is a specific implementation e.g. string, float, enumeration, it will check if the input is that implementation
        - if not strict implementation or we cannot know e.g. an address will return None
        """
        if hasattr(self, "NOCHECK") and self.NOCHECK is True:
            return RuntimeError("check cannot be used")
        raise j.exceptions.Value("not implemented")

    def possible(self, value):
        """
        will check if it can be converted to the jumpscale representation, basically the clean works without error
        :return:
        """
        try:
            self.clean(str(value))
            return True
        except Exception as e:
            return False

    def default_get(self):
        if self._default is None:
            raise j.exceptions.Value("self._default cannot be None")
        return self.clean(self._default)

    def clean(self, value):
        """
        """
        raise j.exceptions.Value("not implemented")

    def python_code_get(self, value):
        """
        produce the python code which represents this value
        """
        value = self.clean(value)
        return "'%s'" % value

    def toml_string_get(self, value, key=""):
        """
        will translate to what we need in toml
        """
        if key == "":
            return "'%s'" % (self.clean(value))
        else:
            return "%s = '%s'" % (key, self.clean(value))

    def capnp_schema_get(self, name, nr):
        return "%s @%s :Text;" % (name, nr)


#!!TYPEBASECLASS!!


class TypeBaseObjFactory(TypeBaseClass):
    def __init__(self):
        self.NAME = self.__class__.NAME
        self.BASETYPE = None

    def capnp_schema_get(self, name, nr):
        """
        """
        return "%s @%s :Data;" % (name, nr)

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

    def clean(self, v):
        raise j.exceptions.NotImplemented()


class TypeBaseClassUnserialized(TypeBaseClass):
    """
    needed to make sure that in the schema this one gets to the unserialized dict
    """
