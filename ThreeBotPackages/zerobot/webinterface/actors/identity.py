from Jumpscale import j


class identity(j.baseclasses.threebot_actor):
    @j.baseclasses.actor_method
    def email(self, schema_out=None, user_session=None):
        return j.tools.threebot.me.default.email

    @j.baseclasses.actor_method
    def pubkey(self, schema_out=None, user_session=None):
        return j.tools.threebot.me.default.pubkey

    @j.baseclasses.actor_method
    def name(self, schema_out=None, user_session=None):
        """
        ```out
        name  = ""
        ```
        """

        out = schema_out.new()
        out.name = j.tools.threebot.me.default.tname

        return out
