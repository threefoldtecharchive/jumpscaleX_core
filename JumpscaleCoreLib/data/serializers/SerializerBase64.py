from Jumpscale import j
import base64
from .SerializerBase import SerializerBase

## NOTE from Glen:
## There used to be only the dumps/loads methods,
## for tfchain we however require to be able to decode/encode directly with binary data,
## trying to decode them into an UTF-8 string doesn't work well with the
## random binary data we deal with in nonces of tfchain.
## Feel free however to rename my added encode/decode function, should the naming not be clear enough.


class SerializerBase64(SerializerBase):
    def __init__(self):
        SerializerBase.__init__(self)

    def encode(self, s):
        if j.data.types.string.check(s):
            b = s.encode()
        else:
            b = s
        return base64.b64encode(b)

    def dumps(self, s):
        return self.encode(s).decode()

    def decode(self, b):
        if j.data.types.string.check(b):
            b = b.encode()
        return base64.b64decode(b)

    def loads(self, s):
        return self.decode(s).decode()
