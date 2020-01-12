"""Definition of several collection types (list, dict, set,...)"""

from Jumpscale import j


import struct
from .TypeBaseClasses import TypeBaseClassSerialized


class JSON(TypeBaseClassSerialized):

    NAME = "json"

    def __init__(self, default=None):
        self.BASETYPE = "string"
        self.NOCHECK = True

        if not default:
            self._default = j.baseclasses.dict()
        else:
            self._default = self.clean(default)

    def clean(self, v=None):
        """
        returns to a dict
        :param v:
        :return: allways return the json deserialized
        """
        if not v:
            v = self._default

        if not v:
            return {}

        if isinstance(v, bytes):
            v = j.data.serializers.msgpack.loads(v)
        elif isinstance(v, str):
            if v.strip() == "":
                return {}
            return self.serializer.loads(v)
        elif isinstance(v, j.data.schema._JSXObjectClass):
            return v._ddict

        if isinstance(v, (dict, set, list, int, float)):
            return v

        raise j.exceptions.Value("only support dict,set, list, int,float, JSXObject or string", data=v)

    @property
    def serializer(self):
        return j.data.serializers.json

    def python_code_get(self, val):
        return str(self.clean(val))

    def toData(self, v):
        v = self.clean(v)
        if isinstance(v, j.baseclasses.dict):
            v = v._data
        return self.serializer.dumps(v)

    def fromString(self, v):
        return self.clean(v)

    def toJSON(self, v):
        return self.toData(v)

    def toHR(self, v):
        return self.toString(v)

    def toString(self, v):
        v = self.clean(v)
        if isinstance(v, j.baseclasses.dict):
            return j.data.serializers.json.dumps(v._data, True, True)
        else:
            return j.data.serializers.json.dumps(v, True, True)


class MSGPACK(JSON):
    """Generic msgpack type which represents anything which can be represented by msgpack"""

    NAME = "msgpack"

    @property
    def serializer(self):
        return j.data.serializers.msgpack

    def capnp_schema_get(self, name, nr):
        return "%s @%s :Data;" % (name, nr)


class YAML(JSON):
    """Generic dictionary type for yaml format"""

    NAME = "yaml"

    @property
    def serializer(self):
        return j.data.serializers.yaml


class Dictionary(MSGPACK):
    """Generic dictionary type"""

    NAME = "dict"

    def __init__(self, default=None):
        self.BASETYPE = "dict"
        if not default:
            self._default = j.baseclasses.dict()
        else:
            self._default = self.clean(default)

    def clean(self, v=None):
        """
        returns to a dict
        :param v:
        :return: allways return the json deserialized
        """
        if not v:
            v = self._default

        if not v:
            return {}

        if isinstance(v, bytes):
            v = j.data.serializers.msgpack.loads(v)
        elif isinstance(v, str):
            if v.strip() == "":
                return {}
            v = j.data.serializers.json.loads(v)
        elif isinstance(v, j.data.schema._JSXObjectClass):
            return v._ddict

        if isinstance(v, dict):
            return v

        raise j.exceptions.Value("only support dict, JSXObject or string", data=v)

    def check(self, value):
        try:
            cleaned = self.clean(value)
        except Exception as e:
            return False

        return isinstance(cleaned, dict)


class Set(TypeBaseClassSerialized):

    """
    hash is 2 value list, represented as 2 times 4 bytes
    """

    NAME = "h,set"
    CUSTOM = False

    def __init__(self, default=None):
        self.BASETYPE = "string"
        if not default:
            default = (0, 0)
        self._default = default

    def fromString(self, s):
        """
        return string from a string (is basically no more than a check)
        """
        if not isinstance(s, str):
            raise j.exceptions.Value("Should be string:%s" % s)
        s = self.clean(s)
        return s

    def toString(self, value):
        """
        serialization to intnr:intnr
        :param value:
        :return:
        """
        v0, v1 = self.clean(value)
        return "%s:%s" % (v0, v1)

    def check(self, value):
        return isinstance(value, (list, tuple)) and len(value) == 2

    def clean(self, value, parent=None):
        """
        will do a strip
        """
        if value is None or value == b"":
            return self._default

        def bytesToInt(val):
            if j.data.types.bytes.check(val):
                if len(val) is not 4:
                    raise j.exceptions.Value("hash parts can only be 4 bytes")
                return struct.unpack("I", val)
            else:
                return int(val)

        if isinstance(value, int):
            # there are prob better ways how to do this
            b = struct.pack("L", value)
            r = struct.unpack("II", b)
            return r[1], r[0]

        elif j.data.types.list.check(value):  # or j.data.types.set.check(value):
            # prob given as list or set of 2 which is the base representation
            if len(value) != 2:
                raise j.exceptions.Value("hash can only be list/set of 2")
            v0 = bytesToInt(value[0])
            v1 = bytesToInt(value[1])
            return (v0, v1)

        elif j.data.types.bytes.check(value):
            if len(value) is not 8:
                raise j.exceptions.Value("bytes should be len 8")
            r = struct.unpack("II", value)
            return r[1], r[0]

        elif j.data.types.string.check(value):
            if ":" not in value:
                raise j.exceptions.Value("when string, needs to have : inside %s" % value)
            v0, v1 = value.split(":")
            v0 = int(v0)
            v1 = int(v1)
            return (v0, v1)

        else:
            raise j.exceptions.Value("unrecognized format for hash:%s" % value)

    def capnp_schema_get(self, name, nr):
        return "%s @%s :Text;" % (name, nr)

    def python_code_get(self, value):
        """
        produce the python code which represents this value
        """
        return "'%s'" % self.toString(value)

    def toml_string_get(self, value, key=""):
        """
        will translate to what we need in toml
        """
        if key == "":
            return self.python_code_get(value)
        else:
            return "%s = %s" % (key, self.python_code_get(value))

    def capnp_schema_get(self, name, nr):
        return "%s @%s :Int64;" % (name, nr)

    def toData(self, v):
        """
        first clean then get the data for capnp
        :param v:
        :return:
        """
        o = self.toBytes(v)
        return struct.unpack("L", o)[0]

        # return o[0] * 0xFFFFFFFF + o[1]

    def toBytes(self, v):
        """
        first clean then get the data for capnp
        :param v:
        :return:
        """
        o = self.clean(v)
        return struct.pack("II", o[1], o[0])


# TODO: why do we have a set, from our perspective a set & list should be same for novice users

# class Set(List):
#     '''Generic set type'''
#
#     self.NAME =  'set'
#     BASETYPE = 'set'
#
#     def check(self, value):
#         '''Check whether provided value is a set'''
#         if value == {}:
#             value = {"default"}
#
#         return isinstance(value, set)
#
#     def default_get(self):
#         return set()
#
#     def clean(self, value,parent=None):
#         if not self.check(value):
#             raise j.exceptions.Value("Valid set is required")
#         return value
#
#     def python_code_get(self, value, sort=False):
#         """
#         produce the python code which represents this value
#         """
#         value = self.clean(value)
#         out = "{ "
#         for item in value:
#             out += "%s, " % self.SUBTYPE.python_code_get(item)
#         out = out.strip(",")
#         out += " }"
#         return out
