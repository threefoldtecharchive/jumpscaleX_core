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

    @property
    def explorer(self):
        if not self._explorer:
            self._explorer = self.get(name="explorer", host="localhost")
        return self._explorer

    def sign_data(self, data):
        """
        will sign any data with private key of our local 3bot private key
        :param payload:
        :return:
        """
        n = j.data.nacl.default
        return n.signing_key.sign(data)

    def sign_jsxobject(self, jsxobject):
        """
        jsxobject, json, signature = j.clients.threebot.sign_jsxobject(jsxobject)

        will sign a jsxobject with private key of our local 3bot private key
        :param jsxobject:
        :return:
        """
        # todo: check type
        json = jsxobject._json
        signature = self.sign_data(json)
        return (jsxobject, json, signature)

    def threebot_client_get(self, tid=None, name=None):
        """

        :param tid: threebot id
        :param name:
        :return:
        """
        if name:
            res = self.find(name=name)
        elif tid:
            res = self.find(tid=tid)
        else:
            raise j.exceptions.Input("specify name or tid")
        if len(res) == 1:
            return res[0]
        elif len(res) > 1:
            raise j.exceptions.JSBUG("should never be more than 1")

        r = self.threebot_record_get(tid=tid, name=name)
        return self.new(name=r.name, tid=r.tid, host=r.ipaddr, pubkey=r.pubkey)

    def threebot_record_get(self, tid=None, name=None):
        # did not find locally yet lets fetch
        r = self.explorer.client.actors.phonebook.get(tid=tid, name=name)
        if r:

            signature_hex = j.clients.threebot._payload_check(
                name=r.name, email=r.email, ipaddr=r.ipaddr, description=r.description, pubkey_hex=r.pubkey
            )
            if not r.signature == signature_hex:
                raise j.exceptions.Input("threebot record, not valid, signature does not match")

            self.get(name=r.name, tid=r.id, host=r.ipaddr, pubkey=r.pubkey)
            return r

        raise j.exceptions.Input("could not find 3bot: user_id:{user_id} name:{name}")

    def _payload_check(self, id=None, name=None, email=None, ipaddr="", description="", pubkey_hex=None):
        assert name
        assert email
        assert id

        if isinstance(pubkey_hex, bytes):
            pubkey_hex = pubkey_hex.decode()
        assert isinstance(pubkey_hex, str)
        assert len(pubkey_hex) == 64

        pubkey = binascii.unhexlify(pubkey_hex)

        n = j.data.nacl.default

        buffer = BytesIO()
        buffer.write(str(id).encode())
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

    def test(self):
        """
        kosmos 'j.clients.threebot.test()'
        :return:
        """

        r = self.threebot_register("test.test", "test@incubaid.com", ipaddr="localhost")

        # tid = threebotid
        clienttomyself = self.threebot_client_get(tid=r.id)
        # or fetch based on name
        clienttomyself2 = self.threebot_client_get(name="test.test")

        assert clienttomyself2.client.ping()

        self._log_info("test ok")
