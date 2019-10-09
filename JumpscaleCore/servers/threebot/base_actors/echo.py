from Jumpscale import j

JSBASE = j.baseclasses.object


class echo(JSBASE):
    def echo(self, message, user_session, schema_out=None):
        """
        ```schema_in
        message = (S)
        ```
        """
        return message
