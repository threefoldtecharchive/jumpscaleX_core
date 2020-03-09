from Jumpscale import j
from nacl.utils import random

NONCE_SIZE = 32


class UserSessionBase(j.baseclasses.object):
    def _init(self):
        self.nonce = random(NONCE_SIZE)
        self._admin = None
        self.threebot_id = None
        self.threebot_name = None
        self.threebot_circles = []
        self.kwargs = []
        self.response_type = j.data.types.get("e", default="auto,json,capnp,msgpack").clean(0)
        self.content_type = j.data.types.get("e", default="auto,json,capnp,,msgpack").clean(0)

    def is_authenticated(self):
        return self.threebot_id != 0

    def admin_check(self):
        if not self.admin:
            raise j.exceptions.Permission("only admin user can access this method")


class UserSessionAdmin(UserSessionBase):
    def _init(self):
        self._admin = True

    @property
    def admin(self):
        return self._admin

    def admin_check(self):
        return True


class UserSession(UserSessionBase):
    @property
    def threebot_client(self):
        if not self.threebot_name:
            return
        return j.clients.threebot.client_get(threebot=self.threebot_id)

    @property
    def admin(self):
        # FIXME: using j.tools.threebot.me.default is not ok
        # what if we have other identity ?
        if self._admin is None:
            if self.threebot_name == j.tools.threebot.me.default.tname:
                self._admin = True
            elif int(self.threebot_id) == j.tools.threebot.me.default.tid:
                self._admin = True
            elif self.threebot_name in j.tools.threebot.me.default.admins:
                self._admin = True
        return self._admin

    def admin_check(self):
        if not self.admin:
            raise j.exceptions.Permission("only admin user can access this method")
        return True
