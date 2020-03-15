from .SerializerBase import SerializerBase
from Jumpscale import j


class SerializerBlowfish(SerializerBase):
    def __init__(self,):
        SerializerBase.__init__(self)
        self.encrkey = ""
        self.c = None

    def _init(self, encrkey):
        if self.encrkey != encrkey:
            from Crypto.Cipher import Blowfish
            from random import randrange

            self.randrange = randrange
            self.c = Blowfish.new(encrkey, mode=Blowfish.MODE_ECB)
            self.encrkey = encrkey

    def dumps(self, obj, encrkey):
        self._init(encrkey)
        if self.c:
            return self.c.encrypt(self.__pad_file(obj))
        else:
            return obj

    def loads(self, s, encrkey):
        self._init(encrkey)
        if self.c:
            return self.__depad_file(self.c.decrypt(s))
        else:
            return s

    # Blowfish cipher needs 8 byte blocks to work with
    def __pad_file(self, data):
        pad_bytes = 8 - (len(data) % 8)
        for i in range(pad_bytes - 1):
            data += chr(self.randrange(0, 256))
        # final padding byte; % by 8 to get the number of padding bytes
        bflag = self.randrange(6, 248)
        bflag -= bflag % 8 - pad_bytes
        data += chr(bflag)
        return data

    def __depad_file(self, data):
        pad_bytes = ord(data[-1]) % 8
        if not pad_bytes:
            pad_bytes = 8
        return data[:-pad_bytes]
