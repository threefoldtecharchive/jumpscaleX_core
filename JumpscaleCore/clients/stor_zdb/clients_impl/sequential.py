import struct

import redis
from Jumpscale import j
from redis import ResponseError

from ..ZDBClientBase import ZDBClientBase
from ..ZDBAdminClientBase import ZDBAdminClientBase

MODE = "seq"


class ZDBClientSeqMode(ZDBClientBase):
    def _key_encode(self, key):
        if key is None:
            key = ""
        else:
            key = struct.pack("<I", key)
        return key

    def _key_decode(self, key):
        return struct.unpack("<I", key)[0]

    def set(self, data, key=None):
        key1 = self._key_encode(key)
        res = self.redis.execute_command("SET", key1, data)
        if not res:  # data already present and the same, 0-db did nothing.
            return res

        key = self._key_decode(res)
        return key

    def delete(self, key):
        key1 = self._key_encode(key)
        try:
            self.redis.execute_command("DEL", key1)
        except ResponseError as e:
            if str(e).find("Key not found") != -1:
                return
            else:
                raise e

    def get(self, key):
        key = self._key_encode(key)
        return self.redis.execute_command("GET", key)

    def exists(self, key):
        key = self._key_encode(key)
        return self.redis.execute_command("EXISTS", key) == 1


class ZDBClientSeqModeAdmin(ZDBClientSeqMode, ZDBAdminClientBase):
    pass
