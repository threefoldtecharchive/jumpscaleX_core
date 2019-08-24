from .SerializerBase import SerializerBase
import snappy
from Jumpscale import j


class SerializerSnappy(SerializerBase):
    def __init__(self):
        SerializerBase.__init__(self)

    def dumps(self, obj):
        return snappy.compress(obj)

    def loads(self, s):
        return snappy.decompress(s)
