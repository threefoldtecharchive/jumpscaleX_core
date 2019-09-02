from Jumpscale import j
import binascii
from .ThreebotClient import ThreebotClient
from io import BytesIO

JSConfigBase = j.baseclasses.object_config_collection


class ThreebotClientFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.threebot"
    _CHILDCLASS = ThreebotClient

    def _init(self, **kwargs):
        self._explorer = None

    @property
    def explorer(self):
        if not self._explorer:
            self._explorer = self.get(name="explorer", host="localhost")
        return self._explorer

    def sign(self, payload):
        n = j.data.nacl.default
        return n.signing_key.sign(payload)

    def threebot_record_get(self, user_id=None, name=None):
        r = self.explorer.client.actors.phonebook.get(user_id=user_id, name=name)
        j.shell()

    def _payload(self, **kwargs):
        n = j.data.nacl.default
        buffer = BytesIO()
        data = j.data.serializers.json.dumps(kwargs)
        data = data.encode()
        buffer.write(data)
        payload = buffer.getvalue()
        signature = n.sign(payload)  # sign with my nacl key

        return (payload, signature)

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

        pubkey2 = binascii.hexlify(pubkey)
        payload, signature = self._payload(
            name=name, email=email, ipaddr=ipaddr, description=description, pubkey=pubkey2
        )

        # need to show how to use the pubkey to verify the signature & get the data
        assert n.verify(payload, signature, verify_key=pubkey)

        res = cl.client.actors.phonebook.register(payload=payload, signature=signature)

        self.threebot_record_get(user_id=res.id)
        self.threebot_record_get(name=res.name)

        self._log_info("registration of threebot '{name}' done" % locals())

        #
        # buffer = BytesIO()
        # buffer.write(name.encode())
        # buffer.write(email.encode())
        # buffer.write(pubkey)
        # buffer.write(ipaddr.encode())
        # buffer.write(description.encode())
        #
        # # payload = name + email + pubkey + ipaddr + description
        # payload = buffer.getvalue()
        # signature = n.sign(payload)
        #
        # # need to show how to use the pubkey to verify the signature & get the data
        # assert n.verify(payload, signature, verify_key=pubkey)

    def test(self):
        """
        kosmos 'j.clients.threebot.test()'
        :return:
        """

        r = self.threebot_register("test.test", "test@incubaid.com", ipaddr="localhost")
        j.shell()
