from Jumpscale import j
from nacl.public import PrivateKey, SealedBox
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import RawEncoder
import nacl.signing
import nacl.secret
import nacl.utils
import nacl.hash
import nacl.encoding
import hashlib

import binascii


# from .AgentWithKeyname import AgentWithName
import binascii
from nacl.exceptions import BadSignatureError
import sys

JSBASE = j.baseclasses.object
print = j.tools.console.echo
Tools = j.core.tools
MyEnv = j.core.myenv


class NACL(j.baseclasses.object):
    def _init(self, name=None, configure_if_needed=False, **kwargs):
        assert name
        self.name = name
        self._signingkey = None
        self._box = None
        if not Tools.exists(self._path):
            Tools.dir_ensure(self._path)
        if not Tools.exists(self._path_seed):
            if configure_if_needed:
                self.configure(privkey_words=None, generate=True)

    def reset(self):
        self._signingkey = None
        self._box = None

    # we expose the signingkey as a property to
    # make it read-only and prevent the user to overwrite it
    @property
    def signing_key(self):
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
        return binascii.hexlify(self.public_key.encode()).decode()

    @property
    def verify_key_hex(self):
        return binascii.hexlify(self.verify_key.encode()).decode()

    @property
    def box(self):
        """
        box is a used to do symetric encryption
        it uses the local private key
        """
        if not self._box:
            self.load(die=False)
        return self._box

    @property
    def _path(self):
        return "%s/keys/%s" % (MyEnv.config["DIR_CFG"], self.name)

    @property
    def _path_seed(self):
        return "%s/key.priv" % (self._path)

    def _ask_privkey_words(self):
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
            self._keys_generate()
            print("{RED}")
            print("{BLUE}" + self.words + "{RESET}\n")
            print("\n{RED}ITS IMPORTANT TO STORE THIS KEY IN A SAFE PLACE{RESET}")
            if not Tools.ask_yes_no("Did you write the words down and store them in safe place?"):
                j.sal.fs.remove(self._path_seed)
                raise j.exceptions.Operations("WE HAVE REMOVED THE KEY, need to restart this procedure.")
            j.tools.console.clear_screen()

            word3 = self.words.split(" ")[2]

        word3 = self.words.split(" ")[2]
        self.word3_check(word3)

    def word3_check(self, word3):
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
        e.g.
        kosmos 'print(j.data.nacl.default.words)'
        """
        if self._signingkey is None:
            raise j.exceptions.NotFound("seed not found, generate a new key pair fist")
        seed = self.signing_key._seed
        return j.data.encryption.mnemonic.to_mnemonic(seed)

    def _keys_generate(self, words=None):
        """
        Generate an ed25519 signing key
        if words if specified, words are used as seed to rengerate a known key
        if words is None, a random seed is generated
        
        once the key is generated it is stored in chosen path encrypted using the local secret
        """
        if words:
            seed = j.data.encryption.mnemonic.to_entropy(words)
            key = SigningKey(seed)
        else:
            key = SigningKey.generate()
            seed = key._seed

        encrypted_seed = self.encryptSymmetric(seed)
        self._file_write_hex(self._path_seed, encrypted_seed)

        # build in verification
        assert encrypted_seed == self._file_read_hex(self._path_seed)

        self._load_singing_key(die=False)

    def configure(self, privkey_words=None, sshagent_use=None, interactive=None, generate=True, reset=False):
        """

        secret is used to encrypt/decrypt the private key when stored on local filesystem
        privkey_words is used to put the private key back

        will ask for the details of the configuration
        :param: sshagent_use is True, will derive the secret from the private key of the ssh-agent if only 1 ssh key loaded
                                secret needs to be None at that point

        :param: generate if True and interactive is False then will autogenerate a key

        :return: None
        """
        Tools.log("NACL uses path:'%s'" % self._path)

        if interactive is None:
            interactive = j.application.interactive

        if sshagent_use:
            raise j.exceptions.Base("does not work yet")

        if reset:
            self.reset()
            j.sal.fs.remove(self._path_seed)
            self._keys_generate(privkey_words)
        self.load(die=False)

        if self._signingkey is None:
            if privkey_words:
                self._keys_generate(words=privkey_words)
            else:
                if j.sal.fs.exists(self._path_seed):
                    self._log_info("load existing key")
                    self.load()
                    assert self._signingkey
                    return
                # means we did not find the seed yet
                if generate:
                    self._keys_generate()
                elif interactive:
                    self._ask_privkey_words()
                else:
                    self._error_raise("cannot generate private key, was not allowed")

            self.load(die=True)

    def load(self, die=True):
        """
        will load private key from filesystem
        if not possible will exit to shell
        """
        if not j.core.myenv.config["SECRET"]:
            raise j.exceptions.Base("secret should already have been set, do 'jsx check'")
            # j.core.myenv.secret_set() #there is no secret yet

        if False and j.core.myenv.config["SSH_KEY_DEFAULT"]:
            # TODO: ERROR, ssh-agent does not work for signing, can't figure out which key to use
            # here have shortcutted it to not use the ssh-agent but would be nice if it works
            # see also: https://github.com/threefoldtech/jumpscaleX_core/issues/561
            j.core.myenv.sshagent.key_default_name  # will make sure the default sshkey is loaded
            key = j.clients.sshagent.sign("nacl_could_be_anything", hash=True)
        else:
            key = j.core.myenv.config["SECRET"]  # is the hex of sha256 hash, need to go to binary
            assert key.strip() != ""
            key = binascii.unhexlify(key)

        try:
            self._box = nacl.secret.SecretBox(key)  # used to decrypt the private key
        except nacl.exceptions.CryptoError:
            if die:
                self._error_raise("could not use the secret key, maybe wrong one, please use 'jsx check'.")
            else:
                return False

        return self._load_singing_key(die=die)

    def _load_singing_key(self, die=True):

        if not j.sal.fs.exists(self._path_seed):
            if die:
                self._error_raise("could not find the path of the private key, please use 'jsx check' to fix.")
            else:
                return False

        seed = self._file_read_hex(self._path_seed)

        try:
            seed = self.decryptSymmetric(seed)
        except nacl.exceptions.CryptoError:
            if die:
                self._error_raise("could not decrypt the private key, maybe wrong one, please use 'jsx check' to fix.")
            else:
                return False

        self._signingkey = SigningKey(seed)
        return True

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

    def ssh_hash(self, data):
        """
        uses sshagent to sign the payload & then hash result with md5
        :return:
        """
        if j.data.types.string.check(data):
            data = data.encode()
        data2 = self.sign_with_ssh_key(data)
        return j.data.hash.md5_string(data2)

    def encryptSymmetric(self, data, hex=False):
        box = self.box
        res = box.encrypt(self.tobytes(data))
        if hex:
            res = self._bin_to_hex(res).decode()
        return res

    def decryptSymmetric(self, data, hex=False):
        if hex:
            data = self._hex_to_bin(data)
        res = self._box.decrypt(self.tobytes(data))
        return res

    def encrypt(self, data, hex=False, public_key=None):
        """ Encrypt data using the public key
            :param data: data to be encrypted, should be of type binary
            :param public_key: if None, the local public key is used
            @return: encrypted data
        """
        if not public_key:
            public_key = self.public_key
        data = self.tobytes(data)
        sealed_box = SealedBox(public_key)
        res = sealed_box.encrypt(data)
        if hex:
            res = self._bin_to_hex(res)
        return res

    def decrypt(self, data, hex=False, private_key=None):
        """ Decrypt incoming data using the private key
            :param data: encrypted data provided
            :param private_key: if None the local private key is used
            @return decrypted data
        """
        if not private_key:
            private_key = self.private_key

        unseal_box = SealedBox(private_key)
        if hex:
            data = self._hex_to_bin(data)
        return unseal_box.decrypt(data)

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
        signedhex = binascii.hexlify(signed.signature)
        return signedhex

    def verify(self, data, signature, verify_key=""):
        """ data is the original data we have to verify with signature
            signature is Ed25519 64 bytes signature
            verify_key is the verify key, is not specified will use
            your own (the verify key is 32 bytes)
        """
        if verify_key is None or verify_key == "":
            verify_key = self.verify_key
        elif j.data.types.bytes.check(verify_key):
            verify_key = VerifyKey(verify_key)

        try:
            verify_key.verify(data, signature)
        except BadSignatureError:
            return False

        return True

    def sign_with_ssh_key(self, data):
        """ will return 32 byte signature which uses the sshagent
            loaded on your system
            this can be used to verify data against your own sshagent
            to make sure data has not been tampered with

            this signature is then stored with e.g. data and you
            can verify against your own ssh-agent if the data was
            tampered with
        """
        hash = hashlib.sha1(data).digest()
        signeddata = self.agent.sign_ssh_data(hash)
        return self.hash32(signeddata)

    def _file_write_hex(self, path, content):
        j.sal.fs.createDir(j.sal.fs.getDirName(path))
        content = binascii.hexlify(content)
        j.sal.fs.writeFile(path, content)

    def _file_read_hex(self, path):
        content = j.sal.fs.readFile(path)
        content = binascii.unhexlify(content)
        return content

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
