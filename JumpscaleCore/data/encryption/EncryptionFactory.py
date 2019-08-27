from Jumpscale import j

# IMPORTANT
# use functionality in j.clients.ssh to deal with SSH-Agent & getting key info, improve if required
# use j.data.nacl for underlying encryption/decryption/signing when possible
JSBASE = j.baseclasses.object
from .mnemonic.mnemonic import Mnemonic


class EncryptionFactory(j.baseclasses.object):
    """
    EncryptionFactory provides the means to sign, encrypt data using NACL
    """

    __jslocation__ = "j.data.encryption"

    def _init(self, **kwargs):
        self._mnemonic = None

    @property
    def mnemonic(self):
        """
        SEE ALSO https://iancoleman.io/bip39/
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
        """
        if not self._mnemonic:
            self._mnemonic = Mnemonic("english")
        return self._mnemonic

    def mnemonic_to_seed(self, words, passphrase=""):
        """

        j.data.encryption.mnemonic_to_seed

        """

        return self.mnemonic.to_seed(words, passphrase)

    def mnemonic_generate(self, strength=256):
        """
        generate a wordlist for a bip39 mnemonic key
        SEE ALSO https://iancoleman.io/bip39/

        strength = 128, 160, 192, 224, 256

        kosmos 'print(j.data.encryption.mnemonic_generate())'

        """
        return self.mnemonic.generate(strength=strength)

    def sign_short(self, data, keyname, keypath=None):
        """
        Sign data using NACL
            :param data: data to be signed
            :param keyname: filename that contains the private key to encrypt and sign the data
            :param keypath: path of dir of the key file, if None it'll fall back to ~/.ssh
            @return: tuple of signed data and signature used in verification
        """

        encrypted = j.data.nacl.encrypt(data=data, keyname=keyname, keypath=keypath)
        signed, signature = j.data.nacl.sign(encrypted)
        return signed, signature

    def verify_short(self, data, signature, keyname, keypath):
        """
        Verify data using signature
            :param data: signed data to be verified using signature
            :param signature: signature that was used to signed the data
            :param keyname: filename that contains the private key to decrypt and sign the data
            :param keypath: path of dir of the key file, if None it'll fall back to ~/.ssh
            @return original data
        """

        verified_data = j.data.nacl.verify(data, signature)
        return j.data.nacl.decrypt(data=verified_data, keyname=keyname, keypath=keypath)

    def test(self):
        """
        kosmos 'j.data.encryption.test()'
        """
        words = "sound key uncover anger liberty coffee now huge catalog bread link grit"
        secret = j.data.encryption.mnemonic_to_seed(words, "1234")
        assert (
            secret
            == b"b \xf8MS$\xe4\x8aV\x8dDk\x0c\x87\xda\xc3\x0b8\xac\xe39\x98\xdf\xa2\xc5P\xdd^\x90.\riq\xc4\xf18\x05(\x87u\xb3\xf3\xac\xf7\xa6C\x05\xe9\x94\xe7\x01\xfb2\xc9B\x14\xa8%S\n\xa7n%\xe7"
        )

        words = "talent army language kick harbor crash quote sick twist enact neutral speak slight artefact copper because capable humble fiscal stamp claw salute credit horse"
        secret = j.data.encryption.mnemonic_to_seed(words, "1234")

        m = self.mnemonic

        # is not very good bin string, but good to test because is readable
        h = b"1234567890123456"
        words2 = m.to_mnemonic(h)
        h2 = m.to_entropy(words2)
        assert h == h2
