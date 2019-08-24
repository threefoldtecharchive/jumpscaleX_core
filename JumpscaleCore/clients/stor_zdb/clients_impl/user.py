from ..ZDBClientBase import ZDBClientBase
from ..ZDBAdminClientBase import ZDBAdminClientBase


class ZDBClientUserMode(ZDBClientBase):
    def set(self, data, key):
        return self.redis.execute_command("SET", key, data)


class ZDBClientUserModeAdmin(ZDBClientUserMode, ZDBAdminClientBase):
    pass
