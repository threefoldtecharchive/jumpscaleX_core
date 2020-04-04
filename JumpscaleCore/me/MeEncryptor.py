from Jumpscale import j
from nacl.public import PrivateKey, SealedBox, Box
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import RawEncoder
import nacl.signing
import nacl.secret
import nacl.utils
import nacl.hash
import nacl.encoding
import hashlib

import binascii
from nacl.exceptions import BadSignatureError
import sys

JSBASE = j.baseclasses.object
print = j.tools.console.echo
Tools = j.core.tools
MyEnv = j.core.myenv


class MeEncryptor(j.baseclasses.object):
    def _init(self, me, **kwargs):
        self.me = me
        self.name = self.me.name
        assert len(self.me.secret) == 32
        self.box = nacl.secret.SecretBox(self.me.secret)
        self.reset()

    def reset(self):
        self._signingkey = None

    @property
    def signing_key(self):
        if not self._signingkey:
            self._priv_key_load()
        return self._signingkey

    @property
    def verify_key(self):
        return self.signing_key.verify_key

    @property
    def private_key(self):
        return self.signing_key.to_curve25519_private_key()

    @property
    def public_key(self):
        return self.signing_key.verify_key.to_curve25519_public_key()

    @property
    def public_key_hex(self):
        return self._bin_to_hex(self.public_key.encode()).decode()

    @property
    def verify_key_hex(self):
        key = self.verify_key.encode()
        key2 = self.encryptSymmetric(key)
        return self._bin_to_hex(key2).decode()

    def words_ask(self):
        """
        :param privkey_words:
        :return:
        """
        msg = """
        There is no private key on your system yet.
        We will generate one for you or you can provide words of your secret key.
        """
        if Tools.ask_yes_no("Ok to generate private key (Y or 1 for yes, otherwise provide words)?"):
            print("\nWe have generated a private key for you.")
            print("\nThe private key:\n\n")
            self._priv_key_generate()
            print("{RED}")
            print("{BLUE}" + self.words + "{RESET}\n")
            print("\n{RED}ITS IMPORTANT TO STORE THIS KEY IN A SAFE PLACE{RESET}")
            if not Tools.ask_yes_no("Did you write the words down and store them in safe place?"):
                raise j.exceptions.Operations("WE HAVE REMOVED THE KEY, need to restart this procedure.")
            j.tools.console.clear_screen()

            word3 = self.words.split(" ")[2]

        word3 = self.words.split(" ")[2]
        self._word3_check(word3)

        return self.verify_key_hex

    def _word3_check(self, word3):
        try:
            word3_to_check = j.tools.console.askString("give the 3e word of the private key string")
            if not word3 == word3_to_check:
                print("the control word was not correct, please try again")
                return self.word3_check(word3)
        except KeyboardInterrupt:
            j.sal.fs.remove(self._path_seed)
            print("WE HAVE REMOVED THE KEY, need to restart this procedure.")

    @property
    def words(self):
        """
        """
        if self._signingkey is None:
            raise j.exceptions.NotFound("seed not found, generate a new key pair first")
        seed = self.signing_key._seed
        return j.data.encryption.mnemonic.to_mnemonic(seed)

    def words_set(self, words):
        seed = j.data.encryption.mnemonic.to_entropy(words)
        self._signingkey = SigningKey(seed)
        self.me.privkey = self.verify_key_hex
        self.me.pubkey = self.public_key_hex

    def _priv_key_generate(self):
        """
        Generate an ed25519 signing key
        if words if specified, words are used as seed to rengerate a known key
        if words is None, a random seed is generated

        once the key is generated it is stored in chosen path encrypted using the local secret
        """
        key = SigningKey.generate()
        # seed = key._seed
        # encrypted_seed = self.encryptSymmetric(seed)
        self._signingkey = key
        self.me.privkey = self.verify_key_hex
        self.me.pubkey = self.public_key_hex
        self._priv_key_load()
        return self.verify_key_hex

    def _priv_key_load(self, die=True):
        seed = self._hex_to_bin(self.me.privkey)
        try:
            seed2 = self.decryptSymmetric(seed)
        except nacl.exceptions.CryptoError:
            if die:
                self._error_raise("could not decrypt the private key.")
            return
        self._signingkey = SigningKey(seed2)

    def _hash(self, data):
        m = hashlib.sha256()
        if not j.data.types.bytes.check(data):
            data = data.encode()
        m.update(data)
        return m.digest()

    def tobytes(self, data):
        if not j.data.types.bytes.check(data):
            data = data.encode()  # will encode utf8
        return data

    def hash32(self, data):
        m = hashlib.sha256()
        m.update(self.tobytes(data))
        return m.digest()

    def hash8(self, data):
        # shortcut, maybe better to use murmur hash
        m = hashlib.sha256()
        m.update(self.tobytes(data))
        return m.digest()[0:8]

    def encryptSymmetric(self, data, hex=False):
        box = self.box
        res = box.encrypt(self.tobytes(data))
        if hex:
            res = self._bin_to_hex(res).decode()
        return res

    def decryptSymmetric(self, data, hex=False):
        if hex:
            data = self._hex_to_bin(data)
        res = self.box.decrypt(self.tobytes(data))
        return res

    def encryptAsymmetric(self, public_key, plaintext, nonce=None, encoder=RawEncoder):
        """
        Encrypts the plaintext message using the given `nonce` (or generates
        one randomly if omitted) and returns the ciphertext encoded with the
        encoder.
        Uses a Box, created using public_key and self.private_key, to encrypt the data.

        :param public_key: public key used to encrypt and
        decrypt messages
        :type public_key: nacl.public.PublicKey
        :param plaintext: The plain text message to encrypt
        :type plaintext: str
        :param nonce: The nonce to use in the encryption, defaults to None
        :type nonce: bytes, optional
        :param encoder:  The encoder to use to encode the ciphertext, defaults to RawEncoder
        :type encoder: nacl encoder, optional
        :return: encrypted plaintext
        :rtype: nacl.utils.EncryptedMessage
        """
        public_key = self._public_key_get(public_key)
        box = Box(self.private_key, public_key)
        return box.encrypt(plaintext, nonce, encoder)

    def _public_key_get(self, public_key):
        if not isinstance(public_key, nacl.public.PublicKey):
            if isinstance(public_key, str) and len(public_key) == 64:
                keyb = self._hex_to_bin(public_key)
                public_key = nacl.public.PublicKey(keyb)
            else:
                raise j.exceptions.Input("public key needs to be hex 64 char's representation or nacl pubkey obj")
        return public_key

    def decryptAsymmetric(self, public_key, ciphertext, nonce=None, encoder=RawEncoder):
        """Decrypts the ciphertext using the `nonce` (explicitly, when passed as a
        parameter or implicitly, when omitted, as part of the ciphertext) and
        returns the plaintext message.

        :param public_key: public key used to encrypt and
        decrypt messages
        :type public_key: nacl.public.PublicKey
        :param ciphertext: The ciphered message to decrypt
        :type ciphertext: bytes
        :param nonce: The nonce used when encrypting the
            ciphertext, default to None
        :type nonce: bytes, optional
        :type encoder: nacl encoder, optional
        :return: decrypted ciphertext
        :rtype: bytes
        """
        public_key = self._public_key_get(public_key)
        box = Box(self.private_key, public_key)
        return box.decrypt(ciphertext, nonce, encoder)

    # def encrypt(self, data, hex=False, public_key=None):
    #     """ Encrypt data using the public key
    #         :param data: data to be encrypted, should be of type binary
    #         :param public_key: if None, the local public key is used
    #         @return: encrypted data
    #     """
    #     if not public_key:
    #         public_key = self.public_key
    #     data = self.tobytes(data)
    #     sealed_box = SealedBox(public_key)
    #     res = sealed_box.encrypt(data)
    #     if hex:
    #         res = self._bin_to_hex(res)
    #     return res
    #
    # def decrypt(self, data, hex=False, private_key=None):
    #     """ Decrypt incoming data using the private key
    #         :param data: encrypted data provided
    #         :param private_key: if None the local private key is used
    #         @return decrypted data
    #     """
    #     if not private_key:
    #         private_key = self.private_key
    #
    #     unseal_box = SealedBox(private_key)
    #     if hex:
    #         data = self._hex_to_bin(data)
    #     return unseal_box.decrypt(data)

    def sign(self, data):
        """
        sign using your private key using Ed25519 algorithm
        the result will be 64 bytes
        """
        if isinstance(data, str):
            data = data.encode()
        signed = self.signing_key.sign(data)
        return signed.signature

    def sign_hex(self, data):
        """
        sign using your private key using Ed25519 algorithm
        the result will be 128 bytes
        """
        if isinstance(data, str):
            data = data.encode()
        signed = self.signing_key.sign(data)
        signedhex = self._bin_to_hex(signed.signature)
        return signedhex

    def _verify_key_get(self, verify_key=None):
        if isinstance(verify_key, nacl.signing.VerifyKey):
            return verify_key
        elif verify_key is None or verify_key == "":
            return self.verify_key
        elif j.data.types.bytes.check(verify_key):
            return VerifyKey(verify_key)
        elif isinstance(verify_key, str) and len(verify_key) == 64:
            keyb = self._hex_to_bin(verify_key)
            return VerifyKey(keyb)
        else:
            raise j.exceptions.Input("public key needs to be hex 64 char's representation or nacl pubkey obj")

    def verify(self, data, signature, verify_key=""):
        """ data is the original data we have to verify with signature
            signature is Ed25519 64 bytes signature
            verify_key is the verify key, is not specified will use
            your own (the verify key is 32 bytes)
        """
        verify_key = self._verify_key_get(verify_key)
        try:
            verify_key.verify(data, signature)
        except BadSignatureError:
            return False

        return True

    # def sign_with_ssh_key(self, data):
    #     """ will return 32 byte signature which uses the sshagent
    #         loaded on your system
    #         this can be used to verify data against your own sshagent
    #         to make sure data has not been tampered with
    #
    #         this signature is then stored with e.g. data and you
    #         can verify against your own ssh-agent if the data was
    #         tampered with
    #     """
    #     hash = hashlib.sha1(data).digest()
    #     signeddata = self.agent.sign_ssh_data(hash)
    #     return self.hash32(signeddata)

    def _bin_to_hex(self, content):
        return binascii.hexlify(content)

    def _hex_to_bin(self, content):
        content = binascii.unhexlify(content)
        return content

    def _error_raise(self, msg):
        raise j.exceptions.Base(msg)

    def __str__(self):
        return "nacl:%s" % self.name

    __repr__ = __str__
