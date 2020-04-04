import nacl

from Jumpscale import j

JSConfigBase = j.baseclasses.object_config


class ThreebotMe(JSConfigBase):
    """
    represents me
    """

    _SCHEMATEXT = """
    @url = jumpscale.threebot.me
    name** = ""
    tid** =  0 (I)                  #my threebot id
    tname** = "me" (S)              #my threebot name
    email = "" (S)
    privkey = ""
    pubkey = ""                     
    admins = (LS)                   #3bot names which are admin of this 3bot
    """

    def _init(self, **kwargs):
        # the threebot config name always corresponds with the config name of nacl, is by design
        self.nacl = j.data.nacl.get(name=self.name)
        self.serialization_format = "json"
        if not self.name:
            raise j.exceptions.Input(
                "threebot.me not filled in, please do j.tools.threebot.init_my_threebot(interactive=True)"
            )

        self._model.trigger_add(self._update_data)

    def _update_data(self, model, obj, action, propertyname):
        if propertyname == "admins" or action == "set_pre":
            # make sure we have 3bot at end if not specified
            r = []
            change = False
            for admin in self.admins:

                if admin.strip() == "":
                    change = True
                    continue
                if len(admin) < 5:
                    raise j.exceptions.Input("admin needs to be more than 4 letters.")
                if "." not in admin:
                    change = True
                    admin += ".3bot"
                r.append(admin)
            if change:
                self.admins = r
        if action == "set_post":
            j.shell()

    # def sign(self, data):
    #     raise
    #     # TODO: implement
    #
    # def data_send_serialize(self, threebot, data):
    #     """
    #     data to send to a threebot needs to be encrypted with pub key of the threebot
    #     the data is unencrypted (a list of values or the value), default serialization = json
    #     :param threebot:
    #     :param data:
    #     :return:
    #     """
    #     return j.tools.threebot._serialize_sign_encrypt(
    #         data=data, serialization_format=self.serialization_format, threebot=threebot, nacl=self.nacl
    #     )
    #
    # def data_received_unserialize(self, threebot, data, signature):
    #     """
    #     data which came from a threebot needs to be unserialized and verified
    #     the data comes in encrypted
    #     :param threebot:
    #     :param data:
    #     :param signature: is the verification key in hex
    #     :return:
    #     """
    #     return j.tools.threebot._deserialize_check_decrypt(
    #         data=data,
    #         serialization_format=self.serialization_format,
    #         threebot=threebot,
    #         verifykey_hex=signature,
    #         nacl=self.nacl,
    #     )

    def configure(self):
        return self.edit()

    # def sign(self, data):
    #     raise
    #     # TODO: implement
    #
    # def data_send_serialize(self, threebot, data):
    #     """
    #     data to send to a threebot needs to be encrypted with pub key of the threebot
    #     the data is unencrypted (a list of values or the value), default serialization = json
    #     :param threebot:
    #     :param data:
    #     :return:
    #     """
    #     return j.tools.threebot._serialize_sign_encrypt(
    #         data=data, serialization_format=self.serialization_format, threebot=threebot, nacl=self.nacl
    #     )
    #
    # def data_received_unserialize(self, threebot, data, signature):
    #     """
    #     data which came from a threebot needs to be unserialized and verified
    #     the data comes in encrypted
    #     :param threebot:
    #     :param data:
    #     :param signature: is the verification key in hex
    #     :return:
    #     """
    #     return j.tools.threebot._deserialize_check_decrypt(
    #         data=data,
    #         serialization_format=self.serialization_format,
    #         threebot=threebot,
    #         verifykey_hex=signature,
    #         nacl=self.nacl,
    #     )
