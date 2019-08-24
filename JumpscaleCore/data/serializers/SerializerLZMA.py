import pylzma
from .SerializerBase import SerializerBase
from Jumpscale import j


class SerializerLZMA(SerializerBase):
    def __init__(self):
        SerializerBase.__init__(self)

    def dumps(self, obj):
        return pylzma.compress(obj)

    def loads(self, s):
        return pylzma.decompress(s)
