from Jumpscale import j
from .RsyncServer import RsyncServer

JSConfigs = j.baseclasses.object_config_collection_testtools


class RsyncFactory(JSConfigs):
    """
    Rsync factory
    """

    __jslocation__ = "j.servers.rsync"
    _CHILDCLASS = RsyncServer

    def install(self, reset=False):
        """
        kosmos 'j.servers.rsync.install()'
        kosmos 'j.servers.rsync.install(reset=True)'
        :return:
        """
        j.builders.system.rsync.install(reset=reset)
