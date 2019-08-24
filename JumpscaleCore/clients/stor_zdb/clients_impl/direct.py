from ..ZDBClientBase import ZDBClientBase
from ..ZDBAdminClientBase import ZDBAdminClientBase


class ZDBClientDirectMode(ZDBClientBase):
    def __init__(self, nsname, factory=None, addr="localhost", port=9900, secret="123456", admin_secret=None):
        super().__init__(factory=factory, addr=addr, port=port, mode="direct", nsname=nsname, secret=secret)


class ZDBClientDirectModeAdmin(ZDBClientDirectMode, ZDBAdminClientBase):
    pass
