from Jumpscale import j

JSBaseConfig = j.baseclasses.object_config


class UserSession(j.baseclasses.object):
    def _init(self):
        self.threebot_id = None
        self.threebot_name = None
        self.threebot_circles = []
        self.return_format = j.data.types.get("e", default="json,msgpack").clean(0)
