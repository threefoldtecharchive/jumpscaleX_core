import imp
import os
import nacl

from Jumpscale import j
from redis.connection import ConnectionError

JSConfigBase = j.baseclasses.object_config
from .WGBase import WGBase


class WGClient(JSConfigBase, WGBase):
    _SCHEMATEXT = """
        @url = jumpscale.wireguard.client.1
        name* = "main"        
        sshclient_name = "" (S)  #if empty then local
        key_private_ = "" (S)
        key_public = "" (S) 
        """

    def __init__(self, **kwargs):
        WGBase.__init__(self, **kwargs)
        JSConfigBase.__init__(self, **kwargs)

    def configure(self):
        if self.key_private_ == "" or self.key_public == "":
            self.key_private_, self.key_public = self.parent.key_pair_get()
            self.save()

    def config_save(self):
        j.shell()

    # def install(self):
    #     j.shell()
    #     if self.islocal:
    #         j.sal.process.execute("brew install wireguard-tools")
    #     pass


class WGClients(j.baseclasses.factory):
    _CHILDCLASS = WGClient
    _name = "clients"
