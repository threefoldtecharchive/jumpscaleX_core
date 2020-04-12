import os
import sys

os.environ["LC_ALL"] = "en_US.UTF-8"

__all__ = ["identity", "secret", "email", "words", "reset"]


class Args:
    def __init__(self):
        self.identity = None
        self.secret = None
        self.email = None
        self.words = None

    def __str__(self):
        out = ""
        out += f" - identity : {self.identity}\n"
        out += f" - secret : {self.secret}\n"
        out += f" - email  : {self.email}\n"
        out += f" - words  : {self.words}\n"

    __repr__ = __str__


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
    words as used for the encryption key
    """
    if not val:
        return args.words
    else:
        args.words = val


def reset():
    """
    reset your arguments for your identity  (secret remains)s
    """
    args.identity = None
    args.email = None
    args.words = None


def str():
    print("Arguments:\n\n")
    print(args)
