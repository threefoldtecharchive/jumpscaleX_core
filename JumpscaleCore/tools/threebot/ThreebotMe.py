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
    tname** = "" (S)                #my threebot name
    email = "" (S)                  #for caching purposes
    pubkey = ""                     #for caching purposes
    """

    def _init(self, **kwargs):
        # the threebot config name always corresponds with the config name of nacl, is by design
        self.nacl = j.data.nacl.get(name=self.name)
        self.serialization_format = "json"
        if not self.name:
            raise j.exceptions.Input(
                "threebot.me not filled in, please do j.tools.threebot.init_my_threebot(interactive=True)"
            )

    def data_send_serialize(self, threebot, data):
        """
        data to send to a threebot needs to be encrypted with pub key of the threebot
        the data is unencrypted (a list of values or the value), default serialization = json
        :param threebot:
        :param data:
        :return:
        """
        return j.tools.threebot._serialize_sign_encrypt(
            data=data, serialization_format=self.serialization_format, threebot=threebot, nacl=self.nacl
        )

    def data_received_unserialize(self, threebot, data, signature):
        """
        data which came from a threebot needs to be unserialized and verified
        the data comes in encrypted
        :param threebot:
        :param data:
        :param signature: is the verification key in hex
        :return:
        """
        return j.tools.threebot._deserialize_check_decrypt(
            data=data,
            serialization_format=self.serialization_format,
            threebot=threebot,
            verifykey_hex=signature,
            nacl=self.nacl,
        )
