from Jumpscale import j

from .NACL import NACL
import nacl.secret
import nacl.utils
import base64
import hashlib
from io import BytesIO
from nacl.public import PrivateKey, SealedBox
import fakeredis
import binascii
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


JSBASE = j.baseclasses.object


class NACLFactory(j.baseclasses.object):
    __jslocation__ = "j.data.nacl"

    def _init(self, **kwargs):
        self._default = None

        # check there is core redis
        if isinstance(j.core.db, fakeredis.FakeStrictRedis):
            j.clients.redis.core_get()

    def configure(self, name="default", privkey_words=None, sshagent_use=None, generate=True, interactive=False):
        """
        secret is used to encrypt/decrypt the private key when stored on local filesystem
        privkey_words is used to put the private key back

        will ask for the details of the configuration
        :param: sshagent_use is True, will derive the secret from the private key of the ssh-agent if only 1 ssh key loaded
                                secret needs to be None at that point
        :param: generate if True and interactive is False then will autogenerate a key

        :return: None

        """
        n = self.get(name=name, load=False)
        n.configure(privkey_words=privkey_words, sshagent_use=sshagent_use, generate=generate, interactive=interactive)
        return n

    def get(self, name="default", load=True, configure_if_needed=True):
        """

        :param name: name of the nacl config
        :param load: if the keys need to be loaded
        :param configure_if_needed: if key path does not exist will generate a key automatically
        :return:
        """
        n = NACL(name=name, configure_if_needed=configure_if_needed)
        if load:
            n.load()
        return n

    def payload_build(self, *args):
        """
        build a bytesIO buffer with all arguments serialized to somethign repeatable
        :param args:
        :return:
        """
        buffer = BytesIO()
        for item in args:
            if isinstance(item, str):
                item = item.encode()
            elif isinstance(item, int) or isinstance(item, float):
                item = str(item).encode()
            elif isinstance(item, bytes):
                pass
            elif isinstance(item, j.data.schema._JSXObjectClass):
                item = item._json
            elif isinstance(item, j.baseclasses.dict):
                item = j.data.serializers.json.dumps(item._data).encode()
            elif item == None:
                raise j.exceptions.Input("should not be None")
            else:
                item = j.data.serializers.json.dumps(item).encode()
            buffer.write(item)
        return buffer.getvalue()

    def payload_sign(self, *args, nacl=None):
        """
        :param nacl: the nacl from the author, by default  j.data.nacl.default
        :param args: what needs to be serialized in same order and signed
        :return: 128 chars hexstring
        """

        if not nacl:
            nacl = j.data.nacl.default

        payload = self.payload_build(*args)

        signature = nacl.sign(payload)
        return binascii.hexlify(signature).decode()

    def verifykey_obj_get(self, verifykey):
        if isinstance(verifykey, VerifyKey):
            return verifykey
        if len(verifykey) == 64:
            verifykey = binascii.unhexlify(verifykey)
        return VerifyKey(verifykey)

    def pubkey_obj_get(self, verifykey):
        verifykey = self.verifykey_obj_get(verifykey)
        return verifykey.to_curve25519_public_key()

    def payload_verify(self, *args, verifykey=None, signature=None, die=True):
        """
        :param args:
        :param verifykey:
        :param signature: 64 bytes or 128 bytes hex encoded (binascii.hexlify)
        :param die:
        :return: True if ok, False if failed or die when die==True
        """
        payload = self.payload_build(*args)
        self._log_debug("payload", data=payload)
        assert signature
        assert verifykey
        assert len(signature) == 64 or len(signature) == 128

        verifykey = self.verifykey_obj_get(verifykey)

        if len(signature) == 128:
            signature = binascii.unhexlify(signature)

        try:
            verifykey.verify(payload, signature)
        except BadSignatureError:
            if die:
                raise j.exceptions.Input("cannot verify payload")
            return False
        return True

    def payload_encrypt_pubkey(self, payload, verifykey=None, hex=False):
        assert verifykey
        pubkey = self.pubkey_obj_get(verifykey)

        sealed_box = SealedBox(pubkey)
        res = sealed_box.encrypt(payload)
        if hex:
            res = self._bin_to_hex(res)
        return res

    @property
    def default(self):
        if self._default is None:
            self._default = self.get()
        return self._default

    def test_signatures(self):
        """
        kosmos 'j.data.nacl.test_signatures()'
        """
        j.data.nacl.configure("test_a", generate=True, interactive=False)
        j.data.nacl.configure("test_b", generate=True, interactive=False)
        nacl_a = j.data.nacl.get("test_a")
        nacl_b = j.data.nacl.get("test_b")

        args = ["a", 1, "astring"]

        payload = j.data.nacl.payload_build(*args)  # you can't do anything with payload, its only useful for signing

        signature = j.data.nacl.payload_sign(*args, nacl=nacl_a)

        assert j.data.nacl.payload_verify(*args, verifykey=nacl_a.verify_key_hex, signature=signature)
        assert j.data.nacl.payload_verify(*args, verifykey=nacl_a.verify_key, signature=signature)
        assert j.data.nacl.payload_verify(*args, verifykey=nacl_a.verify_key.encode(), signature=signature)

        encrypted = j.data.nacl.payload_encrypt_pubkey(payload, verifykey=nacl_b.verify_key_hex)
        encrypted2 = j.data.nacl.payload_encrypt_pubkey(payload, verifykey=nacl_b.verify_key.encode())

        assert nacl_b.decrypt(encrypted) == payload
        assert nacl_b.decrypt(encrypted2) == payload

        print("OK")

    def test(self):
        """
        kosmos 'j.data.nacl.test()'
        """
        cl = self.default  # get's the default location & generate's keys

        data = b"something"
        r = cl.sign(data)

        assert cl.verify(data, r)
        assert cl.verify(b"a", r) == False

        pubsignkey32 = cl.verify_key.encode()

        assert cl.verify(data, r, pubsignkey32)

        a = cl.encryptSymmetric("something")
        b = cl.decryptSymmetric(a)

        assert b == b"something"

        a = cl.encryptSymmetric("something")
        b = cl.decryptSymmetric(a)
        assert b == b"something"

        a = cl.encryptSymmetric("something")
        b = cl.decryptSymmetric(a)
        assert b == b"something"

        a = cl.encryptSymmetric(b"something")
        b = cl.decryptSymmetric(a)
        assert b == b"something"

        # now with hex
        a = cl.encryptSymmetric(b"something", hex=True)
        b = cl.decryptSymmetric(a, hex=True)
        assert b == b"something"

        a = cl.encrypt(b"something")
        b = cl.decrypt(a)

        assert b == b"something"

        a = cl.encrypt("something")  # non binary start
        b = cl.decrypt(a)

        # now with hex
        a = cl.encrypt("something", hex=True)  # non binary start
        b = cl.decrypt(a, hex=True)
        assert b == b"something"

        # test asymetric encryptoin between 2 users
        bob_sk = nacl.public.PrivateKey.generate()

        # alice send a message to bob, encrypt the message with the public of bob
        message = b"hello world"
        encrypted = cl.encrypt(message, public_key=bob_sk.public_key)
        # bob decrypt the message with its private key
        decrypted = cl.decrypt(encrypted, private_key=bob_sk)
        assert message == decrypted
        # ensure no one else can read it
        foo_sk = nacl.public.PrivateKey.generate()
        try:
            cl.decrypt(encrypted, foo_sk)
            raise j.exceptions.Base("should have given error")
        except:
            pass

        # LETS NOW TEST THAT WE CAN START FROM WORDS

        words = j.data.nacl.default.words
        j.sal.fs.copyDirTree("/sandbox/cfg/keys/default", "/sandbox/cfg/keys/default_backup")  # make backup
        j.sal.fs.remove("/sandbox/cfg/keys/default")
        try:
            self.default.reset()
            try:
                self.default.load()
                raise j.exceptions.Base("should have given error")
            except:
                pass

            self.default._keys_generate(words=words)
            self.default.load()

            b = cl.decrypt(a, hex=True)
            assert b == b"something"

        finally:
            j.sal.fs.copyDirTree("/sandbox/cfg/keys/default_backup", "/sandbox/cfg/keys/default")
            j.sal.fs.remove("/sandbox/cfg/keys/default_backup")

        self._log_info("TEST OK")
        print("TEST OK")

    def test_perf(self):
        """
        kosmos 'j.data.nacl.test_perf()'
        """

        cl = self.default  # get's the default location & generate's keys
        data = b"something"

        nr = 10000
        j.tools.timer.start("signing")
        for i in range(nr):
            p = str(i).encode()
            r = cl.sign(data + p)
        j.tools.timer.stop(i)

        nr = 10000
        j.tools.timer.start("encode and verify")
        for i in range(nr):
            p = str(i).encode()
            r = cl.sign(data + p)
            assert cl.verify(data + p, r)
        j.tools.timer.stop(i)

        nr = 10000
        data2 = data * 20
        j.tools.timer.start("encryption/decryption assymetric")
        for i in range(nr):
            a = cl.encrypt(data2)
            b = cl.decrypt(a)
            assert data2 == b
        j.tools.timer.stop(i)
