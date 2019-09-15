import nacl

from Jumpscale import j

JSConfigBase = j.baseclasses.object_config


class ThreebotClient(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.threebot.client
    name** = ""                      #is the bot dns
    tid** =  0 (I)                     #threebot id
    host = "127.0.0.1" (S)          #for caching purposes
    port = 8901 (ipport)            #for caching purposes
    pubkey = ""                     #for caching purposes
    """

    def _init(self, **kwargs):
        self._gedis = None
        assert self.name != ""

    @property
    def client(self):
        if not self._gedis:
            self._gedis = j.clients.gedis.get(name=self.name, host=self.host, port=self.port)
        return self._gedis

    def ping(self):
        return self.client.ping()

    # def auth(self, bot_id):
    #     nacl_cl = j.data.nacl.get()
    #     nacl_cl._load_privatekey()
    #     signing_key = nacl.signing.SigningKey(nacl_cl.privkey.encode())
    #     epoch = str(j.data.time.epoch)
    #     signed_message = signing_key.sign(epoch.encode())
    #     cmd = "auth {} {} {}".format(bot_id, epoch, signed_message)
    #     res = self._redis.execute_command(cmd)
    #     return res

    def threebot_wallet_create(self, name, sender_signature_hex):
        """

        the threebot will create a wallet for you as a user and you can leave money on there to be used for
        paying services on the threefold network

        if a wallet stays empty during 1 day it will be removed automatically

        :param: name is the name of the 3bot like how will be used in following functions like threebot_register_name
        :param: sender_signature_hex off the name as done by private key of the person who asks

        :return: a TFT wallet address
        """
        # just to be 100% transparant to other implementation we will only use the redis client implementation
        # TODO: needs to be implemented
        return ""

    def threebot_name_register(self, name, tft_transaction_id, sender_signature_hex):
        """

        is the first step of a registration, this is the step where money is involved.
        without enough funding it won't happen. The cost is 20 TFT today to register a name.

        :param: name you want to register can eg $name.$extension of $name if no extension will be $name.3bot
                needs to correspond on the name as used in threebot_wallet_create
        :param: sender_signature_hex signed by private key of the sender

        each name registration costs 100 TFT

        :return:
        """
        self._log_info("register step1: for 3bot name: %s" % name)
        cl = self.explorer
        cl.ping()

    def threebot_record_register(self, name, pubkey, ipaddr, sender_signature_hex, email="", description=""):
        """

        :param: name you want to register can eg $name.$extension of $name if no extension will be $name.3bot
                needs to correspond on the name as used in threebot_wallet_create
        :param email:
        :param ipaddr:
        :param description:
        :return:
        """
        self._log_info("register: {name} {email} {ipaddr}" % locals())
        n = j.data.nacl.default
        pubkey = n.verify_key.encode()
        self._log(pubkey)

        cl = self.explorer
        cl.ping()

        # FOR ENCRYPTION WITH PUB KEY
        # import nacl
        # from nacl.signing import VerifyKey
        #
        # vk = VerifyKey(pubkey)
        # pubkey_obj = vk.to_curve25519_public_key()
        # encrypted = n.encrypt(b"a", hex=False, public_key=pubkey_obj)
        # n.decrypt(encrypted)

        if not isinstance(pubkey, bytes):
            raise j.exceptions.Input("needs to be bytes")

        pubkey_hex = binascii.hexlify(pubkey)
        signature_hex = self._payload_check(
            name=name, email=email, ipaddr=ipaddr, description=description, pubkey_hex=pubkey_hex
        )

        res = cl.client.actors.phonebook.register(
            name=name, email=email, ipaddr=ipaddr, description=description, pubkey=pubkey_hex, signature=signature_hex
        )

        record0 = self.threebot_record_get(tid=res.id)
        record1 = self.threebot_record_get(name=res.name)

        self._log_info("registration of threebot '{name}' done" % locals())

        return record1
