"""configurable arguments"""
import os
import pytoml
import binascii
import nacl.secret
import hashlib
from .core import core
from . import english

os.environ["LC_ALL"] = "en_US.UTF-8"

__all__ = ["identity", "secret", "email", "words", "reset", "explorer"]


class Args(core.IT.Tools._BaseClassProperties):
    def _init(self, **kwargs):
        self._identity = None
        self.secret = None
        self.email = None
        self.words = None
        self.explorer = None
        self._key = "3sdk:data"

    def reset(self):
        self.identity = None
        self.email = None
        self.words = None
        self.explorer = None

    def ask_secret(self):
        return core.IT.Tools.ask_password("please provide secret (to locally encrypt your container)")

    @property
    def identity(self):
        return self._identity

    @identity.setter
    def identity(self, value):
        identitydata = _load_identity(value)
        if not identitydata:
            self._identity = value
            return
        self.email = identitydata["email"]
        # try to decode words
        if not self.secret:
            self.secret = self.ask_secret()

        binarykey = binascii.unhexlify(identitydata["signing_key"])
        while True:
            try:
                secrethash = hashlib.md5(self.secret.encode()).hexdigest()
                box = nacl.secret.SecretBox(secrethash.encode())
                seed = box.decrypt(binarykey)
                break
            except nacl.exceptions.CryptoError:
                print(
                    "Failed to decrypt your key with this secret, please enter the correct key or ctrl+c to interrupt"
                )
                self.secret = self.ask_secret()

        self.words = core.IT.Tools.to_mnemonic(seed, english.words)
        self._identity = value


args = Args()


def _load_identity(identity):
    identitydir = core.IT.MyEnv.config["DIR_IDENTITY"]
    identityfile = os.path.join(identitydir, "identities", f"{identity}.toml")
    if os.path.exists(identityfile):
        with open(identityfile) as fd:
            return pytoml.load(fd)


def identity(val=""):
    """
    you can have multiple identities,
    you need to specify an identity for many operations we do e.g. creating a container
    if the identity exists all other variables will be loaded from it
    """
    if not val:
        return args.identity
    else:
        args.identity = val


def secret(val=""):
    """
    the secret passphrase as used for encrypting all data
    """
    if not val:
        return args.secret
    else:
        args.secret = val


def email(val=""):
    if not val:
        return args.email
    else:
        args.email = val


def words(val=""):
    """
    words as used for the encryption key retrieved from 3bot connect app
    """
    if not val:
        if args.words:
            return args.words
        else:
            from .container import _containers

            if _containers.IT.DockerFactory.container_name_exists("3bot"):
                c = _containers.get(name="3bot")
                c.execute("print(j.me.encryptor.words);print(\n\n)", jumpscale=True)
            else:
                print(" - ERROR: cannot retrieve words, container 3bot not found.")
    else:
        args.words = val


def explorer(val=""):
    """
    explorer to use
    """
    if not val:
        return args.explorer
    else:
        args.explorer = val


def reset():
    """
    reset your arguments for your identity  (secret remains)s
    """
    args.reset()


def __str__():
    return f"Arguments:\n\n{args}"


identity.__property__ = True
secret.__property__ = True
email.__property__ = True
words.__property__ = True
explorer.__property__ = True
