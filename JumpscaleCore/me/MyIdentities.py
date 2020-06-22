from Jumpscale import j
import binascii
from .Me import Me
import nacl
import binascii


class MyIdentities(j.baseclasses.object_config_collection):
    _CHILDCLASS = Me
    _classname = "myidentities"

    def _init(self, **kwargs):
        self._box = None
        self.secret_expiration_hours = 24 * 30 * 12

    def secret_set(self, secret=None, confirm=True):
        """
        can be the hash or the originating secret passphrase
        """
        j.core.myenv.secret_set(secret=secret, confirm=confirm)
        self._box = None

    @property
    def secret(self):
        secret = j.core.myenv.secret_get()
        if not isinstance(secret, bytes):
            secret = secret.encode()
        return secret

    @property
    def box(self):
        if not self._box:
            self._box = nacl.secret.SecretBox(self.secret)
        return self._box

    def exists(self, tname):
        basepath = j.core.tools.text_replace("{DIR_BASE}/myhost/identities")
        return j.sal.fs.exists(f"{basepath}/{tname}.toml")

    @property
    def me(self):
        """
        your default threebot identity

        to configure:

        kosmos 'j.me.configure()'

        :return:
        """
        DEFAULT_PATH = j.core.tools.text_replace("{DIR_BASE}/myhost/identities/default")
        default_identity = None
        if j.sal.fs.exists(DEFAULT_PATH):
            default_identity = j.sal.fs.readFile(DEFAULT_PATH).strip("\n")
        return self.get(name="default", tname=default_identity)

    def encrypt(self, data, hex=False):
        res = self.box.encrypt(self._tobytes(data))
        if hex:
            res = self._bin_to_hex(res).decode()
        return res

    def decrypt(self, data, hex=False):
        if hex:
            data = self._hex_to_bin(data)
        res = self.box.decrypt(self._tobytes(data))
        return res

    def _bin_to_hex(self, content):
        return binascii.hexlify(content)

    def _hex_to_bin(self, content):
        content = binascii.unhexlify(content)
        return content

    def _tobytes(self, data):
        if not j.data.types.bytes.check(data):
            data = data.encode()  # will encode utf8
        return data

    def get(self, name="default", id=None, **kwargs):
        return j.baseclasses.object_config_collection.get(self, name=name, id=id, autosave=False, **kwargs)

    def test(self):
        """
        kosmos 'j.myidentities.test()'
        """

        # means test will not ask questions
        j.application.interactive = False

        id1 = self.get("test_id1")
        id2 = self.get("test_id2")

        # should already be set, if not test cannot run
        assert id1.secret

        id1.tname = "kdstest1.test"
        id2.tname = "kdstest2.test"
        id1.email = "something1@info.com"
        id2.email = "something2@info.com"

        id1.configure_sshkey(generate=True)
        id2.configure_sshkey(generate=True)

        # test symmetric encryption
        encrypted = id1.encryptor.encrypt("a")
        res = id1.encryptor.decrypt(encrypted)
        assert res == b"a"

        id1.configure_encryption(generate=True)
        id2.configure_encryption(generate=True)

        r1 = id1.encryptor.encrypt(b"a", public_key=id2.encryptor.public_key)
        r2 = id1.encryptor.encrypt(b"b", public_key=id2.encryptor.public_key_hex)
        r3 = id1.encryptor.decrypt(r1, public_key=id2.encryptor.public_key)
        r4 = id1.encryptor.decrypt(r2, public_key=id2.encryptor.public_key_hex)
        assert r3 == b"a"
        assert r4 == b"b"

        r1 = id1.encryptor.encrypt(b"a", verify_key=id2.encryptor.verify_key)
        r2 = id1.encryptor.encrypt(b"b", verify_key=id2.verify_key)  # is in hex
        r3 = id1.encryptor.decrypt(r1, verify_key=id2.encryptor.verify_key)
        r4 = id1.encryptor.decrypt(r2, verify_key=id2.verify_key)
        assert r3 == b"a"
        assert r4 == b"b"

        signature = id1.encryptor.sign_hex(b"a")
        id2.encryptor.verify(b"a", signature, verify_key=id2.encryptor.verify_key)
        id2.encryptor.verify(b"a", signature, verify_key=id2.encryptor.verify_key_hex)
        id2.encryptor.verify(b"a", signature, verify_key=id2.verify_key)

        assert len(signature) == 128

        id1.delete()
        id2.delete()
