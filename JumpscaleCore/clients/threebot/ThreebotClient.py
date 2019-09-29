import nacl

from Jumpscale import j
import binascii

JSConfigBase = j.baseclasses.object_config
from nacl.signing import VerifyKey
from nacl.public import PrivateKey, PublicKey, SealedBox


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
        self._pubkey_obj = None
        self._verifykey_obj = None
        self._sealedbox_ = None
        self._gedis_connections = {}
        assert self.name != ""

    def actors_get(self, namespace="default"):
        if not namespace in self._gedis_connections:
            g = j.clients.gedis.get(name=self.name, host=self.host, port=self.port, namespace=namespace)
            self._gedis_connections[namespace] = g
        return self._gedis_connections[namespace].actors

    def reload(self):
        for key, g in self._gedis_connections.items():
            g.reload()

    @property
    def _gedis(self):
        a = self.actors_get("default")
        return self._gedis_connections["default"]

    @property
    def actors_default(self):
        return self.actors_get("default")

    def ping(self):
        return self.client.ping()

    def encrypt_for_threebot(self, data, hex=False):
        """
        Encrypt data using the public key of the remote threebot
        :param data: data to be encrypted, should be of type binary

        @return: encrypted data hex or binary

        """
        if isinstance(data, str):
            data = data.encode()
        res = self._sealedbox.encrypt(data)
        if hex:
            res = binascii.hexlify(res)
        return res

    def verify_from_threebot(self, data, signature, data_is_hex=False):
        """
        :param data, if string will unhexlify else binary data to verify against verification key of the threebot who send us the data

        :return:
        """
        if isinstance(data, str) or data_is_hex:
            data = binascii.unhexlify(data)
        if len(signature) == 128:
            signature = binascii.unhexlify(signature)
        return self.verifykey_obj.verify(data, signature=signature)

    @property
    def _sealedbox(self):
        if not self._sealedbox_:
            self._sealedbox_ = SealedBox(self.pubkey_obj)
        return self._sealedbox_

    @property
    def pubkey_obj(self):
        if not self._pubkey_obj:
            self._pubkey_obj = self.verifykey_obj.to_curve25519_public_key()
        return self._pubkey_obj

    @property
    def verifykey_obj(self):
        if not self._verifykey_obj:
            assert self.pubkey
            verifykey = binascii.unhexlify(self.pubkey)
            assert len(verifykey) == 32
            self._verifykey_obj = VerifyKey(verifykey)
        return self._verifykey_obj

    # def auth(self, bot_id):
    #     nacl_cl = j.data.nacl.get()
    #     nacl_cl._load_privatekey()
    #     signing_key = nacl.signing.SigningKey(nacl_cl.privkey.encode())
    #     epoch = str(j.data.time.epoch)
    #     signed_message = signing_key.sign(epoch.encode())
    #     cmd = "auth {} {} {}".format(bot_id, epoch, signed_message)
    #     res = self._redis.execute_command(cmd)
    #     return res
