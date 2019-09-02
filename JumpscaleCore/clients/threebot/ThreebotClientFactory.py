from Jumpscale import j
import binascii
from .ThreebotClient import ThreebotClient
from io import BytesIO
from nacl.signing import VerifyKey

JSConfigBase = j.baseclasses.object_config_collection


class ThreebotClientFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.threebot"
    _CHILDCLASS = ThreebotClient

    def _init(self, **kwargs):
        self._explorer = None
        self.reset()

    @property
    def explorer(self):
        if not self._explorer:
            self._explorer = self.get(name="explorer", host="localhost")
        return self._explorer

    def sign(self, payload):
        n = j.data.nacl.default
        return n.signing_key.sign(payload)

    def reset(self):
        self.threebot_records = j.baseclasses.dict()

    def threebot_record_get(self, user_id=None, name=None):
        if user_id in self.threebot_records:
            return self.threebot_records[user_id]
        r = self.explorer.client.actors.phonebook.get(user_id=user_id, name=name)
        if r:

            signature_hex = j.clients.threebot._payload_check(
                name=r.name, email=r.email, ipaddr=r.ipaddr, description=r.description, pubkey_hex=r.pubkey
            )
            if not r.signature == signature_hex:
                raise j.exceptions.Input("threebot record, not valid, signature does not match")
            self.threebot_records[r.id] = r
            return r

        raise j.exceptions.Input("could not find 3bot: user_id:{user_id} name:{name}")

    def _payload_check(self, name=None, email=None, ipaddr="", description="", pubkey_hex=None):
        assert name
        assert email

        if isinstance(pubkey_hex, bytes):
            pubkey_hex = pubkey_hex.decode()
        assert isinstance(pubkey_hex, str)
        assert len(pubkey_hex) == 64

        pubkey = binascii.unhexlify(pubkey_hex)

        n = j.data.nacl.default

        buffer = BytesIO()
        buffer.write(name.encode())
        buffer.write(email.encode())
        buffer.write(ipaddr.encode())
        buffer.write(description.encode())
        buffer.write(pubkey_hex.encode())

        # payload = name + email + pubkey + ipaddr + description
        payload = buffer.getvalue()
        signature = n.sign(payload)

        signature_hex = binascii.hexlify(signature).decode()

        # need to show how to use the pubkey to verify the signature & get the data
        assert n.verify(payload, signature, verify_key=pubkey)

        return signature_hex

    def threebot_register(self, name, email, ipaddr="", description="", pubkey=None):
        self._log_info("register: {name} {email} {ipaddr}" % locals())
        n = j.data.nacl.default
        if not pubkey:
            pubkey = n.verify_key.encode()
        self._log(pubkey)

        cl = j.clients.threebot.get("registrar")
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

        self.threebot_record_get(user_id=res.id)
        record = self.threebot_record_get(name=res.name)

        self._log_info("registration of threebot '{name}' done" % locals())

        return record

    def test(self):
        """
        kosmos 'j.clients.threebot.test()'
        :return:
        """

        r = self.threebot_register("test.test", "test@incubaid.com", ipaddr="localhost")
        j.shell()
