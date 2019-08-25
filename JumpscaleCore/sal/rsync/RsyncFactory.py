from Jumpscale import j

from .Rsync import *

JSBASE = j.baseclasses.object


class RsyncFactory(j.baseclasses.object):
    """
    """

    __jslocation__ = "j.sal.rsync"

    def getServer(self, root):
        return RsyncServer(root)

    def getClient(self, name="", addr="localhost", port=873, login="", passwd=""):
        return RsyncClient(name, addr, port, login, passwd)

    def getClientSecret(self, addr="localhost", port=873, secret=""):
        return RsyncClientSecret(addr, port, secret)


# TODO: *2 there seems to be overlap here, multiple files not on right location
