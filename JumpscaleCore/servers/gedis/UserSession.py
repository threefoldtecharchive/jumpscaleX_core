from Jumpscale import j


class UserSessionBase(j.baseclasses.object):
    pass


class UserSessionAdmin(UserSessionBase):
    def _init(self):
        self.admin = True
        self.threebot_id = None
        self.threebot_name = None
        self.threebot_circles = []
        self.kwargs = []
        self.response_type = j.data.types.get("e", default="auto,json,msgpack").clean(0)
        self.content_type = j.data.types.get("e", default="auto,json,msgpack").clean(0)
        self.threebot_client = None

    def admin_check(self):
        return True


class UserSession(UserSessionBase):
    def _init(self):
        self._admin = None
        self.threebot_id = 0
        self.threebot_name = None
        self.threebot_circles = []
        self.kwargs = []
        self.response_type = j.data.types.get("e", default="auto,json,msgpack").clean(0)
        self.content_type = j.data.types.get("e", default="auto,json,msgpack").clean(0)

    @property
    def threebot_client(self):
        if not self.threebot_name:
            return
        return j.clients.threebot.client_get(threebot=self.threebot_id)

    @property
    def admin(self):
        if self._admin is None:
            if self.threebot_name == j.myidentities.me.default.tname:
                self._admin = True
            elif int(self.threebot_id) == j.myidentities.me.default.tid:
                self._admin = True
            elif self.threebot_name in j.myidentities.me.default.admins:
                self._admin = True
        return self._admin

    def admin_check(self):
        if not self.admin:
            raise j.exceptions.Permission("only admin user can access this method")
