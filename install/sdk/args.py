"""configurable arguments"""
from MyEnv import MyEnv

myenv = MyEnv()


__all__ = ["identity", "secret", "email", "words", "reset"]

from BaseClassProperties import BaseClassProperties


class Args(BaseClassProperties):
    def _init(self, db=None, **kwargs):
        self.identity = None
        self.secret = None
        self.email = None
        self.words = None
        self._key = "3sdk:data"
        self._load


args = Args(db=myenv.db)


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

            if myenv.docker.container_name_exists("3bot"):
                c = _containers.get(name="3bot")
                c.execute("print(j.me.encryptor.words);print(\n\n)", jumpscale=True)
            else:
                print(" - ERROR: cannot retrieve words, container 3bot not found.")
    else:
        args.words = val


def reset():
    """
    reset your arguments for your identity  (secret remains)s
    """
    args.identity = None
    args.email = None
    args.words = None


def __str__():
    return f"Arguments:\n\n{args}"


identity.__property__ = True
secret.__property__ = True
email.__property__ = True
words.__property__ = True
