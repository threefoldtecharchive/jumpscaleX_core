from Jumpscale import j

JSBASE = j.baseclasses.object


class base(JSBASE):
    def _init(self, **kwargs):
        self.server = kwargs["gedis_server"]
        self.format = "json"

    def _return_format(self, out):
        return getattr(out, f"_{self.format}")

    def format_configure(self, format_type):
        if format_type not in ["json", "msgpack"]:
            raise j.exceptions.Input("format_type needs to be either json or msgpack")
        self.format = format_type

    def identify(self, seed_encrypted, schema_out=None, user_session=None):
        """
        :seed_encrypted: a random seed as given by the client, encrypted by private key of client
        :return: "$threebotid:$signature"

        $signature is bytesignature in hex format of "$seed:$threebotid"
        this can be used by the client who asks identity

        """
        out = schema_out.new()
        nacl = j.data.nacl.default

        assert isinstance(seed_encrypted, bytes)
        toencode = "%s:%s" % (seed, j.core.myenv.config["THREEBOT_ID"])
        signature = j.tools.threebot.sign_data(toencode.encode())
        out.server_id = j.core.myenv.config["THREEBOT_ID"]
        return self._return_format(out)

    def phonebook_get(self, threebot_id, schema_out=None, user_session=None):
        """
        ```in
        threebot_id = (I)
        ```

        ```out
        name = (S)
        email = (S)
        pubkey = (S)
        ipaddr = (S)
        description = (S)
        signature = (S)
        ```
        """
        client = self.server.client_get()
        if not getattr(client.actors, "phonebook", None):
            raise j.exceptions.RuntimeError("phonebook actor not added to server")
        out = client.actors.phonebook.get(threebot_id)
        return self._return_format(out)

    # def authorize(self, threebot_id, signature):
