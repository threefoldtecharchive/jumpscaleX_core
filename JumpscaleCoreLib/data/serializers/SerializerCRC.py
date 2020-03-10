# import struct
from Jumpscale import j

JSBASE = j.baseclasses.object


class SerializerCRC(j.baseclasses.object):
    def __init__(self):
        JSBASE.__init__(self)

    def dumps(self, obj):
        j.data.hash.crc32_string(obj)
        return obj

    def loads(self, s):
        return s[4:]
