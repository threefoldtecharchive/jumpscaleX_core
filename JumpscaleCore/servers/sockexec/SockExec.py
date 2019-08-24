import os
from Jumpscale import j
import netstr
import socket
import time


class SockExec(j.application.JSBaseDataObjClass):

    __jslocation__ = "j.servers.sockexec"

    _SCHEMATEXT = """
           @url =  jumpscale.servers.sockexec.1
           name* = "default" (S)
           socketpath = "/sandbox/var/exec.sock"
           """

    def _init(self, **kwargs):
        self._startupcmd = None

    def start(self):
        """
        Starts sonic server in tmux
        """
        self._log_info("start sockexec server")
        self.stop()
        self.startupcmd.start()

    def stop(self):
        self._log_info("stop sockexec server")
        self.startupcmd.stop()

    @property
    def startupcmd(self):
        if not self._startupcmd:
            if not j.core.tools.cmd_installed("sockexec"):
                raise j.exceptions.Base("cannot find command sockexec, please install")
            cmd = "rm -f /sandbox/var/exec.sock;sockexec %s" % self.data.socketpath
            self._startupcmd = j.servers.startupcmd.get("sockexec", cmd_start=cmd)
            self._startupcmd.executor = "background"
            self._startupcmd.process_strings_regex = ["^sockexec"]

        return self._startupcmd

    def install(self, reset=False):
        j.builders.apps.sockexec.install(reset=reset)

    def execute(self, cmd, wait=True):
        # need better way to return the result, how to use the socket well???
        # https://github.com/jprjr/sockexec
        args = cmd.split(" ")
        if not os.path.exists(self.socketpath):
            raise j.exceptions.Base("cannot find exec socket path:%s" % path)
        self.client = socket.socket(socket.AF_UNIX)
        self.client.connect(self.socketpath)
        s = netstr.encode(str(len(args)).encode())
        for cmd in args:
            s += netstr.encode(cmd.encode())
        s += netstr.encode(b"")
        self.client.sendall(s)
        res = []
        r = b""
        while wait:
            r += self.client.recv(1024)
            while b"," in r:
                splitted = r.split(b",")
                if len(splitted) > 0:
                    r2 = netstr.decode(splitted[0] + b",")
                    res.append(r2)
                    r = b",".join(splitted[1:])
            if len(res) > 2 and b"exitcode" == res[-2]:
                return res
            time.sleep(0.01)

    def test(self, reset=False):
        """
        kosmos 'j.servers.sockexec.test()'
        :return:
        """
        self.install(reset=reset)
        self.start()
        assert j.servers.startupcmd.sockexec.is_running()
        res = self.execute("ls /")
        assert len(res) == 4
        self.stop()
        assert j.servers.startupcmd.sockexec.is_running() == False
        print("test ok")
