from Jumpscale import j


class html_test(j.baseclasses.threebot_actor):
    @j.baseclasses.actor_method
    def hello(self, name_, user_session, schema_out=None):
        """
        :param name: name to say hello to

        ```in
        name_ = (S)
        ```

        ```out
        content = (S)
        ```
        """
        out = schema_out.new()
        out.content = f"Hello <h3>{name_}</h3>"
        return out

    @j.baseclasses.actor_method
    def hello_markdown(self, name_, user_session, schema_out=None):
        """
        :param name: name to say hello to

        ```in
        name_ = (S)
        ```

        ```out
        content = (S)
        ```
        """
        out = schema_out.new()
        out.content = f"_markdown test_ Hello `{name_}`"
        return out
