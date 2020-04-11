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
from io import BytesIO
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
        self.reset()
        self._tools = None

    @property
    def tools(self):
        """
        these are a variety of tools to do serialization with encryption
        """
        if not self._tools:
            from .EncryptorTools import EncryptorTools

            self._tools = EncryptorTools(self)
        return self._tools

    def reset(self):
        self._signing_key = None

    @property
    def signing_key(self):
        if not self._signing_key:
            self._signing_key_load()
        return self._signing_key

    @property
    def signing_key_hex(self):
        key2 = j.myidentities.encrypt(self._signing_key.encode())
        return self._bin_to_hex(key2).decode()

    @property
    def verify_key(self):
        return self.signing_key.verify_key

    @property
    def verify_key_hex(self):
        return self._bin_to_hex(self.verify_key.encode()).decode()

    @property
    def private_key(self):
        return self.signing_key.to_curve25519_private_key()

    @property
    def public_key(self):
        return self.signing_key.verify_key.to_curve25519_public_key()

    @property
    def public_key_hex(self):
        return self._bin_to_hex(self.public_key.encode()).decode()

    def words_ask(self):
        """
        :param signing_key_words:
        :return:
        """
        msg = """
        There is no private key on your system yet.
        We will generate one for you or you can provide words of your secret key.
        """
        if Tools.ask_yes_no("Ok to generate private key (Y or 1 for yes, otherwise provide words)?"):
            print("\nWe have generated a private key for you.")
            print("\nThe private key:\n\n")
            self._signing_key_generate()
            print("{RED}")
            print("{BLUE}" + self.words + "{RESET}\n")
            print("\n{RED}ITS IMPORTANT TO STORE THIS KEY IN A SAFE PLACE{RESET}")
            if not Tools.ask_yes_no("Did you write the words down and store them in safe place?"):
                raise j.exceptions.Operations("WE HAVE REMOVED THE KEY, need to restart this procedure.")
            j.tools.console.clear_screen()

            word3 = self.words.split(" ")[2]

            word3 = self.words.split(" ")[2]
            self._word3_check(word3)

        else:
            while True:
                words = Tools.ask_string("give your words for your private key:")
                try:
                    self.words_set(words)
                    return self.signing_key_hex
                except Exception as e:
                    print(str(e))

        return self.signing_key_hex

    def _word3_check(self, word3):
        try:
            word3_to_check = j.tools.console.askString("give the 3e word of the private key string")
            if not word3 == word3_to_check:
                print("the control word was not correct, please try again")
                self._word3_check(word3)
        except KeyboardInterrupt:
            j.sal.fs.remove(self._path_seed)
            print("WE HAVE REMOVED THE KEY, need to restart this procedure.")

    @property
    def words(self):
        """
        """
        self.private_key
        self.signing_key_hex
        if self._signing_key is None:
            raise j.exceptions.NotFound("seed not found, generate a new key pair first")
        seed = self.signing_key._seed
        return j.data.encryption.mnemonic.to_mnemonic(seed)

    def words_set(self, words):
        seed = j.data.encryption.mnemonic.to_entropy(words)
        self._signing_key = SigningKey(seed)
        self.me.signing_key = self.signing_key_hex
        self.me.verify_key = self.verify_key_hex

    def _signing_key_generate(self):
        """
        Generate an ed25519 signing key
        if words if specified, words are used as seed to rengerate a known key
        if words is None, a random seed is generated

        once the key is generated it is stored in chosen path encrypted using the local secret
        """
        key = SigningKey.generate()
        # seed = key._seed
        # encrypted_seed = j.myidentities.encrypt(seed)
        self._signing_key = key
        self.me.signing_key = self.signing_key_hex
        self.me.verify_key = self.verify_key_hex
        self._signing_key_load()

        self.me.save()

    def _signing_key_load(self, die=True):
        seed = self._hex_to_bin(self.me.signing_key)
        try:
            seed2 = j.myidentities.decrypt(seed)
        except nacl.exceptions.CryptoError:
            if die:
                self._error_raise("could not decrypt the private key.")
            return
        self._signing_key = SigningKey(seed2)

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

    def encrypt(self, plaintext, public_key=None, verify_key=None, nonce=None, encoder=RawEncoder):
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
        public_key = self._public_key_get(public_key=public_key, verify_key=verify_key)
        box = Box(self.private_key, public_key)
        return box.encrypt(plaintext, nonce, encoder)

    def decrypt(self, ciphertext, public_key=None, verify_key=None, nonce=None, encoder=RawEncoder):
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
        public_key = self._public_key_get(public_key=public_key, verify_key=verify_key)
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
            raise j.exceptions.Input("public key needs to be hex 64 char's representation or nacl verify_key obj")

    def _public_key_get(self, public_key=None, verify_key=None):

        if public_key:
            if not isinstance(public_key, nacl.public.PublicKey):
                if isinstance(public_key, str) and len(public_key) == 64:
                    keyb = self._hex_to_bin(public_key)
                    public_key = nacl.public.PublicKey(keyb)
                else:
                    raise j.exceptions.Input(
                        "public key needs to be hex 64 char's representation or nacl verify_key obj"
                    )
        else:
            assert verify_key
            verify_key = self._verify_key_get(verify_key)
            return verify_key.to_curve25519_public_key()

        return public_key

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
        return j.myidentities._bin_to_hex(content)

    def _hex_to_bin(self, content):
        return j.myidentities._hex_to_bin(content)

    def _error_raise(self, msg):
        raise j.exceptions.Base(msg)

    def __str__(self):
        return "nacl:%s" % self.name

    __repr__ = __str__

    def _test_perf(self):
        """
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

        verifykey = self._verifykey_obj_get(verifykey)

        if len(signature) == 128:
            signature = binascii.unhexlify(signature)

        try:
            verifykey.verify(payload, signature)
        except BadSignatureError:
            if die:
                raise j.exceptions.Input("cannot verify payload")
            return False
        return True

    def payload_sign(self, *args, nacl=None):
        """
        :param nacl: the nacl from the author, by default  j.me.encryptor
        :param args: what needs to be serialized in same order and signed
        :return: 128 chars hexstring
        """

        if not nacl:
            nacl = self

        payload = self.payload_build(*args)

        signature = nacl.sign(payload)
        return binascii.hexlify(signature).decode()

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
            elif item is None:
                raise j.exceptions.Input("should not be None")
            else:
                item = j.data.serializers.json.dumps(item).encode()
            buffer.write(item)
        return buffer.getvalue()
