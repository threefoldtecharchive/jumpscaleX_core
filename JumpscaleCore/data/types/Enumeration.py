from Jumpscale import j
from .TypeBaseClasses import *


class EnumerationObj(TypeBaseObjClass):
    def _data_from_init_val(self, value):
        """
        convert init value to raw type inside this object
        :return:
        """
        try:
            value_id = int(value)
        except:
            pass
        if isinstance(value, str):
            if value == "":
                return 0
            else:
                value_str = value.upper().strip()
                if value_str not in self._typebase.values:
                    return 0
                return self._typebase.values.index(value_str) + 1
        elif isinstance(value, int):
            if value > len(self._typebase.values) + 1:
                return 0
            if value == 0:
                return 0
            return value
        else:
            raise j.exceptions.Value("unsupported type for enum, is int or string")
        raise

    @property
    def _string(self):
        if self._data is 0:
            return "UNKNOWN"
        return self._typebase.values[self._data - 1]

    @property
    def _python_code(self):
        return "'%s'" % self._string

    @property
    def value(self):
        return self._data

    @value.setter
    def value(self, val):
        obj = self._typebase.clean(val)
        self._data = obj._data

    def __str__(self):
        return self._string

    __repr__ = __str__

    def __eq__(self, other):
        if other in [None, ""]:
            return False
        try:
            other = self._typebase.clean(other)
        except Exception as e:
            if str(e).find("could not find enum") != -1:
                # means its not even an enumeration we know so need to return False
                return False
            raise e
        return other.value == self.value

    def __dir__(self):
        res = []  # "_string","_python_code","value"
        for item in self._typebase.values:
            res.append(item)
        return res

    def __getattr__(self, item):
        if item in self._typebase.values:
            self._data = self._typebase.values.index(item) + 1
            return self
        return self.__getattribute__(item)


class Enumeration(TypeBaseObjFactory):

    """
    Generic string type
    stored in capnp as int

    0 is unknown (nill)
    1 is the default

    """

    NAME = "enum,enumeration,e"
    CUSTOM = True
    __slots__ = ["values", "_default", "_jsx_location"]

    def __init__(self, default=None):

        values = default  # here the default is used to create custom instance
        if not default:
            raise j.exceptions.Value("enumeration needs default arg to be given e.g. red,blue,... ")

        self.BASETYPE = "int"
        self.NOCHECK = True

        if isinstance(values, str):
            values = values.split(",")
            values = [item.strip().strip("'").strip().strip('"').strip() for item in values]
        if not isinstance(values, list):
            raise j.exceptions.Value("input for enum is comma separated str or list")
        self.values = [item.upper().strip() for item in values]

        self._default = 1

    def capnp_schema_get(self, name, nr):
        return "%s @%s :UInt8;" % (name, nr)

    def toData(self, value):
        o = self.clean(value)
        return o._data

    def clean(self, value):
        """
        can use int or string,
        will find it and return as string
        """
        if value is None:
            return self.default_get()
        if isinstance(value, EnumerationObj):
            return value
        return EnumerationObj(self, value)

    def __dir__(self):
        res = ["clean", "default_get", "toData", "capnp_schema_get"]
        for item in self.values:
            res.append(item)
        return res

    def __getattr__(self, item):
        if item in self.values:
            data = self.values.index(item) + 1
            return self.clean(data)
        return self.__getattribute__(item)

    def __str__(self):
        values = ",".join(self.values)
        return "ENUM: %s (default:%s)" % (values, self.default_get())

    __repr__ = __str__
