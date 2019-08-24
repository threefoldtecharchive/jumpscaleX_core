from Jumpscale import j

# TODO if we use ujson, then we need to refactor the rest of this file
# cause ujson has no JSEncoder propery
# try:
#     import ujson as json
# except BaseException:
# import json
import json
from .SerializerBase import SerializerBase


class BytesEncoder(json.JSONEncoder):

    ENCODING = "ascii"

    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode(self.ENCODING)
        return json.JSONEncoder.default(self, obj)


class Encoder(object):
    @staticmethod
    def get(encoding="ascii"):
        kls = BytesEncoder
        kls.ENCODING = encoding
        return kls


class SerializerUJson(SerializerBase):
    def __init__(self):
        SerializerBase.__init__(self)

    def dumps(self, obj, sort_keys=False, indent=False, encoding="ascii"):
        try:
            return json.dumps(
                obj, ensure_ascii=False, sort_keys=sort_keys, indent=indent, cls=Encoder.get(encoding=encoding)
            )
        except Exception as e:
            raise j.exceptions.Value("Cannot dump (package) json", data=obj, exception=e)

    def loads(self, s):
        if isinstance(s, (bytes, bytearray)):
            s = s.decode("utf-8")

        if isinstance(s, str):
            try:
                return json.loads(s)
            except Exception as e:
                raise j.exceptions.Value("Cannot load json", data=s, exception=e)
