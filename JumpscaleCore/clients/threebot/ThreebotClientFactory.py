from Jumpscale import j
import binascii
from .ThreebotClient import ThreebotClient

JSConfigBase = j.baseclasses.factory


class ThreebotClientFactory(j.baseclasses.factory):
    __jslocation__ = "j.clients.threebot"
    _CHILDFACTORY_CLASS = ThreebotClient

    def _init(self, **kwargs):
        self._explorer = None

    @property
    def explorer(self):
        if not self._explorer:
            self._explorer = self.get(name="explorer", host="134.209.90.92")
        return self._explorer

    def sign(self, payload):
        n = j.data.nacl.default
        return n.signing_key.sign(payload)

    def threebot_record_get(self, user_id=None, name=None):
        r = self.explorer.client.actors.phonebook.get(user_id=user_id, name=name)
        j.shell()

    def threebot_register(self, name, email, ipaddr="", description="", pubkey=None):
        n = j.data.nacl.default
        if not pubkey:
            pubkey = n.verify_key.encode()
        self._log(pubkey)

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

        from io import BytesIO

        buffer = BytesIO()
        buffer.write(name.encode())
        buffer.write(email.encode())
        buffer.write(pubkey)
        buffer.write(ipaddr.encode())
        buffer.write(description.encode())

        # payload = name + email + pubkey + ipaddr + description
        payload = buffer.getvalue()
        signature = n.sign(payload)

        # need to show how to use the pubkey to verify the signature & get the data
        assert n.verify(payload, signature, verify_key=pubkey)

        j.shell()
        asd
        r = self.explorer.client.actors.phonebook.register(name=name, email=email, pubkey=pubkey, signature=signature)

        j.shell()

    def test(self):
        """
        kosmos 'j.clients.threebot.test()'
        :return:
        """

        r = self.threebot_register("test.test", "test@incubaid.com", ipaddr="134.209.90.92")
        j.shell()
