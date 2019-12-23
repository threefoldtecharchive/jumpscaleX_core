from Jumpscale import j

from .ExecutorBase import ExecutorBase


class ExecutorSSH(ExecutorBase):
    def _init3(self, sshclient=None, **kwargs):
        assert sshclient
        self.type = "ssh"
        self.sshclient = sshclient
        self.uid = self.sshclient.uid

        # self.kosmos = self.sshclient.kosmos
        # self.shell = self.sshclient.shell
        self.upload = self.sshclient.upload
        self.download = self.sshclient.download

    def _load(self):
        ExecutorBase._load(self)
        if not self.sshclient.addr:
            raise j.exceptions.Input("ssh client needs to have addr specified")

    def shell(self, cmd=None, interactive=True):
        self._load()
        if cmd:
            j.shell()
        cmd = "ssh {LOGIN}@{ADDR} -A -p {PORT}"
        cmd = self._replace(cmd)
        j.sal.process.executeWithoutPipe(cmd)

    def execute(
        self,
        cmd=None,
        die=True,
        showout=True,
        timeout=1000,
        env=None,
        sudo=False,
        replace=True,
        interactive=False,
        script=False,
    ):
        """
        @RETURN rc, out, err
        """
        self._load()
        if env or sudo:
            raise j.exceptions.NotFound("Not implemented for ssh executor")
            return self.execute(cmd)
        return self.sshclient.execute(
            cmd=cmd, interactive=interactive, showout=showout, replace=replace, die=die, timeout=timeout
        )

    def __repr__(self):
        return "Executor ssh: %s (%s)" % (self.sshclient.addr, self.sshclient.port)

    __str__ = __repr__
