from Jumpscale import j
import binascii
from .Me import Me


class MeIdentities(j.baseclasses.object_config_collection):
    _CHILDCLASS = Me
    _classname = "myidentities"

    @property
    def default(self):
        """
        your default threebot identity
        :return:
        """
        return self.get(name="default")

    def get(self, name="default", id=None, **kwargs):
        return j.baseclasses.object_config_collection.get(self, name=name, id=id, autosave=False, **kwargs)

    def secret_set(self, val=None):
        """
        kosmos 'j.me_identities.secret_set()'
        """
        return self.default.secret_set(val)

    def test(self):
        """
        kosmos 'j.me_identities.test()'
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
        encrypted = id1.encryptor.encryptSymmetric("a")
        res = id1.encryptor.decryptSymmetric(encrypted)
        assert res == b"a"

        id1.configure_privatekey(generate=True)
        id2.configure_privatekey(generate=True)

        r1 = id1.encryptor.encryptAsymmetric(id2.encryptor.public_key, b"a")
        r2 = id1.encryptor.encryptAsymmetric(id2.encryptor.public_key_hex, b"b")

        r3 = id1.encryptor.decryptAsymmetric(id2.encryptor.public_key, r1)
        r4 = id1.encryptor.decryptAsymmetric(id2.encryptor.public_key_hex, r2)

        assert r3 == b"a"
        assert r4 == b"b"

        signature = id1.encryptor.sign_hex(b"a")
        id2.encryptor.verify(b"a", signature, verify_key=id2.encryptor.public_key)
        # id2.encryptor.verify(b"a", signature, verify_key=id2.encryptor.public_key_hex)

        j.shell()
