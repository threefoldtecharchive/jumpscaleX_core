import msgpack
from .SerializerBase import SerializerBase
from Jumpscale import j


class SerializerMSGPack(SerializerBase):
    def __init__(self):
        SerializerBase.__init__(self)

    def dumps(self, obj):
        try:
            return msgpack.packb(obj, use_bin_type=True)
        except Exception as e:
            raise j.exceptions.Value("Cannot dump (package) msgpack", data=obj, exception=e)

    def loads(self, s):
        if isinstance(s, (bytes, bytearray)):
            try:
                return msgpack.unpackb(s, raw=False)
            except Exception as e:  # TODO:need more specific error catching
                raise j.exceptions.Value("Cannot dump (package) msgpack", data=s, exception=e)
        else:
            raise j.exceptions.Value("Cannot loads msgpack, input needs to be bytes", data=s)
