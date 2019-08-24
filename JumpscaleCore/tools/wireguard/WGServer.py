import imp
import os
import nacl

from Jumpscale import j
from redis.connection import ConnectionError

from .WGClient import WGClients
from .WGBase import WGBase


class WGServerFactory(j.application.JSBaseConfigsConfigFactoryClass, WGBase):
    _name = "server"
    _SCHEMATEXT = """
    @url = jumpscale.wireguard.server.1
    name* = "main"
    sshclient_name = "" (S)
    key_private_ = "" (S)
    key_public = "" (S) 
    """
    _CHILDCLASSES = [WGClients]

    def __init__(self, **kwargs):
        WGBase.__init__(self)
        j.application.JSBaseConfigsConfigFactoryClass.__init__(self, **kwargs)

    def _init(self, **kwargs):
        self._config_path = self.executor._replace("{DIR_CFG}/wg0.conf")

    # @property
    # def ssh(self):
    #     if not self._ssh:
    #         self._ssh = j.clients.ssh.get(name=self.sshclient_name, needexist=True)
    #     return self._ssh

    # @property
    # def executor(self):
    #     return self.ssh.executor

    def start(self):
        if not j.core.tools.exists(self._config_path):
            self.install()
            print("- GENERATE WIREGUARD KEY")

            if self.key_private_ == "" or self.key_public == "":
                self.key_private_, self.key_public = self.key_pair_get()
                self.save()

            self.executor.execute("mkdir -p %s" % j.sal.fs.getDirName(self._config_path))

    def configure(self):

        args = {}
        args["WIREGUARD_SERVER_PUBKEY"] = self.key_public
        args["WIREGUARD_SERVER_PRIVKEY"] = self.key_private_
        args["WIREGUARD_PORT"] = 7777

        SERVER = """
        [Interface]
        Address = 10.10.10.1/24
        SaveConfig = true
        PrivateKey = {WIREGUARD_SERVER_PRIVKEY}
        ListenPort = {WIREGUARD_PORT}

        """

        PEER = """
        [Peer]
        PublicKey = {PUBKEY}
        AllowedIPs = 10.10.10.0/24

        """

        CONFIG_OUT = j.core.tools.text_replace(SERVER, args=args)

        for client in self.clients:
            client.configure()
            CONFIG_OUT += j.core.tools.text_replace(PEER, args={"PUBKEY": client.pubkey})
            j.shell()
            w

        # j.core.tools.config_save("/sandbox/cfg/wireguard.toml", config)
        # config = j.core.tools.config_load("/sandbox/cfg/wireguard.toml")

        path = "/tmp/wg0.conf"
        self.executor.file_write(self._config_path, CONFIG_OUT, args=args)
        rc, out, err = self.executor.execute("ip link del dev wg0", showout=False, die=False)
        j.shell()
        cmd = "wg-quick up %s" % path
        self.executor.execute(cmd)
