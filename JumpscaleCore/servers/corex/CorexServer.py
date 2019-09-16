import os
from Jumpscale import j

JSConfigClient = j.baseclasses.object_config


class CorexServer(JSConfigClient):
    _SCHEMATEXT = """
           @url =  jumpscale.servers.corex.1
           name** = "default" (S)
           port = 1500 (I)
           user = "" (S)
           password = "" (S)
           chroot = false (B)
           readonly = false (B)
           interface = ""
           """

    def _init(self, **kwargs):
        self._startupcmd = None

    def start(self):
        """
        Starts sonic server in tmux
        """
        self._log_info("start corex server")
        if not j.core.tools.cmd_installed("corex"):
            raise j.exceptions.Base("install corex: 'j.servers.corex.install()'")
        self.startupcmd.start()

    @property
    def client(self):
        j.clients.corex.default.addr = "localhost"
        j.clients.corex.default.port = self.port
        return j.clients.corex.default

    def stop(self):
        self._log_info("stop corex server")
        self.startupcmd.stop()

    @property
    def startupcmd(self):
        if not self._startupcmd:
            if not j.core.tools.cmd_installed("corex"):
                raise j.exceptions.Base("cannot find command corex, please install")
            cmd = "corex -p %s" % (self.port)
            if self.readonly:
                cmd += " -R"
            if self.interface:
                cmd += " -i %s" % self.interface
            if self.user and self.password:
                cmd += " -c %s:%s" % (self.user, self.password)
            self._startupcmd = j.servers.startupcmd.get("corex_%s" % self.name, cmd_start=cmd, ports=[self.port])
            self._startupcmd.executor = "background"

        return self._startupcmd
