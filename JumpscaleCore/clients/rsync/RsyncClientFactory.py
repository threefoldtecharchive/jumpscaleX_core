from Jumpscale import j
from .RsyncClient import RsyncClient

JSConfigs = j.baseclasses.object_config_collection


class RsyncFactory(JSConfigs):

    """
    Rsync Client factory
    """

    __jslocation__ = "j.clients.rsync"
    _CHILDCLASS = RsyncClient
