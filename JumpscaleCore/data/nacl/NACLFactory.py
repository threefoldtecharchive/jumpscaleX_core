from Jumpscale import j

from .NACL import NACL
import nacl.secret
import nacl.utils
import base64
import hashlib
from nacl.public import PrivateKey, SealedBox
import fakeredis

JSBASE = j.baseclasses.object


class NACLFactory(j.baseclasses.object):
    __jslocation__ = "j.data.nacl"

    def _init(self, **kwargs):
        self._default = None

        # check there is core redis
        if isinstance(j.core.db, fakeredis.FakeStrictRedis):
            j.clients.redis.core_get()

    def configure(self, name="default", privkey_words=None, sshagent_use=None, generate=False, interactive=True):
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

    def get(self, name="default", load=True):
        """
        """
        n = NACL(name=name)
        if load:
            n.load()
        return n

    @property
    def default(self):
        if self._default is None:
            self._default = self.get()
        return self._default

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
