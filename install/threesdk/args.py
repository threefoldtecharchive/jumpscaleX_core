"""configurable arguments"""
import os
from .core import core

os.environ["LC_ALL"] = "en_US.UTF-8"

__all__ = ["identity", "secret", "email", "words", "reset", "explorer"]


class Args(core.IT.Tools._BaseClassProperties):
    def _init(self, **kwargs):
        self.identity = None
        self.secret = None
        self.email = None
        self.words = None
        self.explorer = None
        self._key = "3sdk:data"
        self._load

    def reset(self):
        self.identity = None
        self.email = None
        self.words = None
        self.explorer = None


args = Args()


def identity(val=""):
    """
    you can have multiple identities,
    you need to specify an identity for many operations we do e.g. creating a container
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
