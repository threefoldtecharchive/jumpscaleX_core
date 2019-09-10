"""Definition of several collection types (list, dict, set,...)"""

from Jumpscale import j


import struct
from .TypeBaseClasses import TypeBaseClassUnserialized


class JSON(TypeBaseClassUnserialized):

    NAME = "json"

    def __init__(self, default=None):
        self.BASETYPE = "string"
        self.NOCHECK = True
        if not default:
            default = {}
        self._default = default

    def possible(self, value):
        """
        Check whether provided value is a dict
        """
        if not isinstance(value, str):
            return False
        try:
            j.data.serializers.json.loads(value)
        except ValueError:
            return False
        return True

    def check(self, v):
        try:
            j.data.serializers.json.loads(v)
            return True
        except j.exceptions.Value:
            return False

    def _default_get(self):
        return None

    def clean(self, v=""):
        """
        returns to a dict
        :param v:
        :return:
        """
        if v is None:
            return self._default_get()
        if isinstance(v, dict):
            pass
        elif isinstance(v, str):
            try:
                v = j.data.serializers.json.loads(v)
            except j.exceptions.Value:
                pass
        elif isinstance(v, (set, list, int, float)):
            pass
        elif isinstance(v, j.data.schema._JSXObjectClass):
            v = v._ddict
        else:
            raise j.exceptions.Value("only support dict, JSXObject or string", data=v)
        return v

    def python_code_get(self, val):
        return str(self.clean(val))

    def toData(self, v):
        v = self.clean(v)
        return j.data.serializers.json.dumps(v)

    def fromString(self, v):
        return self.clean(v)

    def toJSON(self, v):
        return self.toData(v)

    def toHR(self, v):
        return self.toString(v)

    def toString(self, v):
        return j.data.serializers.json.dumps(self.clean(v))


class MSGPACK(JSON):
    """Generic msgpack type which represents anything which can be represented by msgpack"""

    NAME = "msgpack"

    def possible(self, value):
        """Check whether provided value is a dict"""
        if not isinstance(value, str):
            return False
        try:
            j.data.serializers.msgpack.loads(value)
        except ValueError:
            return False
        return True

    def toData(self, v):
        v = self.clean(v)
        return j.data.serializers.msgpack.dumps(v)

    def fromString(self, s):
        """
        return string from a dict
        """
        if j.data.types.msgpack.check(s):
            return s
        else:
            j.data.serializers.msgpack.loads(s)
            return s

    def toString(self, v):
        return j.data.serializers.msgpack.dumps(v)


class YAML(JSON):
    """Generic dictionary type for yaml format"""

    NAME = "yaml"

    def possible(self, value):
        """Check whether provided value is a dict"""
        if not isinstance(value, str):
            return False
        try:
            j.data.serializers.yaml.loads(value)
        except ValueError:
            return False
        return True

    def toData(self, v):
        v = self.clean(v)
        return j.data.serializers.yaml.dumps(v)

    def fromString(self, s):
        """
        return string from a dict
        """
        if j.data.types.yaml.check(s):
            return s
        else:
            j.data.serializers.yaml.loads(s)
            return s

    def toString(self, v):
        return j.data.serializers.yaml.dumps(v)


class Dictionary(TypeBaseClassUnserialized):
    """Generic dictionary type"""

    NAME = "dict"

    def __init__(self, default=None):

        self.BASETYPE = "dict"
        if not default:
            default = j.baseclasses.dict()
        self._default = default

    def check(self, value):
        """Check whether provided value is a dict"""
        return isinstance(value, dict) or isinstance(value, j.baseclasses.dict)

    def fromString(self, s):
        """
        return string from a dict
        """
        if j.data.types.dict.check(s):
            return s
        else:
            s = s.replace("''", '"')
            j.data.serializers.json.loads(s)
            return s

    def toData(self, v):
        v = self.clean(v)
        if isinstance(v, j.baseclasses.dict):
            return j.data.serializers.msgpack.dumps(v._data)
        else:
            return j.data.serializers.msgpack.dumps(v)

    def clean(self, v=""):
        """
        supports binary, string & dict
        if binary will use msgpack
        if string will use json
        :param v:
        :return:
        """
        if v is None:
            return self._default_get()
        if j.data.types.bytes.check(v):
            if v == b"":
                v = j.baseclasses.dict()
            else:
                # print(v)
                v = j.data.serializers.msgpack.loads(v)
        elif j.data.types.string.check(v):
            v = j.data.serializers.json.loads(v)
        if not self.check(v):
            raise j.exceptions.Value("dict for clean needs to be bytes, string or dict")
        return v

    def toString(self, v):
        v = self.clean(v)
        if isinstance(v, j.baseclasses.dict):
            return j.data.serializers.json.dumps(v._data, True, True)
        else:
            return j.data.serializers.json.dumps(v, True, True)

    def toJSON(self, v):
        return self.toString(v)

    def python_code_get(self, value):
        """
        produce the python code which represents this value
        """
        return self.toString(value)

    def toHR(self, v):
        return self.toString(v)

    def capnp_schema_get(self, name, nr):
        return "%s @%s :Data;" % (name, nr)


class Set(TypeBaseClassUnserialized):

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

    def clean(self, value):
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
#     def clean(self, value):
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
