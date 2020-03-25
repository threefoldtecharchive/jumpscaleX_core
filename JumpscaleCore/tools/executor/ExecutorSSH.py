from Jumpscale import j

from .ExecutorBase import ExecutorBase


class ExecutorSSH(ExecutorBase):
    def _init3(self, **kwargs):
        assert self.type == "ssh"
        self._sshclient = None
        self.uid = self.sshclient.uid

    def download(self, source, dest=None, ignoredir=None, ignorefiles=None, recursive=True):
        source = self._replace(source)
        dest = j.core.tools.text_replace(dest)
        return self.sshclient.download(
            source=source, dest=dest, ignoredir=ignoredir, ignorefiles=ignorefiles, recursive=recursive
        )

    def upload(
        self,
        source,
        dest=None,
        recursive=True,
        createdir=True,
        rsyncdelete=True,
        ignoredir=None,
        ignorefiles=None,
        keepsymlinks=True,
        retry=4,
    ):
        source = j.core.tools.text_replace(source)
        dest = self._replace(dest)
        return self.sshclient.upload(
            source=source,
            dest=dest,
            recursive=recursive,
            createdir=createdir,
            rsyncdelete=rsyncdelete,
            ignoredir=ignoredir,
            ignorefiles=ignorefiles,
            keepsymlinks=keepsymlinks,
            retry=retry,
        )

    @property
    def sshclient(self):
        if not self._sshclient:
            assert self.connection_name
            self._sshclient = j.clients.ssh.get(name=self.connection_name)
        return self._sshclient

    def shell(self, cmd=None):
        login = self.sshclient.login
        addr = self.sshclient.addr
        port = self.sshclient.port
        if cmd:
            cmd2 = f"ssh {login}@{addr} -A -p {port} '%s'" % cmd
        else:
            cmd2 = f"ssh {login}@{addr} -A -p {port}"
        j.sal.process.executeWithoutPipe(cmd2)

    def mosh(self, cmd=None, ssh_private_key_name=None, interactive=True):
        """
        if private key specified
        :param ssh_private_key:
        :return:
        """
        self.installer.mosh()
        C = j.clients.sshagent._script_get_sshload(keyname=ssh_private_key_name)
        r = self.execute(C, interactive=interactive)
        cmd = "mosh -ssh='ssh -tt -oStrictHostKeyChecking=no -p {PORT}' {LOGIN}@{ADDR} -p 6000:6100 'bash'"
        cmd = self._replace(
            cmd, args={"LOGIN": self.sshclient.login, "ADDR": self.sshclient.addr, "PORT": self.sshclient.port}
        )
        error = False
        try:
            j.sal.process.executeWithoutPipe(cmd)
        except Exception as e:
            error = True
        self.execute("rm -f /tmp/myfile")
        if error:
            raise j.exceptions.Base("cannot start mosh, see error", data=e)

    def _execute_cmd(self, cmd, interactive=True, showout=True, die=True, timeout=3600):
        res = self.sshclient.execute(cmd=cmd, interactive=interactive, showout=showout, die=die, timeout=timeout)
        return res

    def file_read(self, path):
        self._log_debug("file read:%s" % path)
        path = self._replace(path)
        rc, out, err = self.execute("cat %s" % path, showout=False, interactive=False)
        return out

    def file_write(self, path, content, mode=None, owner=None, group=None, showout=True):
        """
        @param append if append then will add to file
        """
        path = self._replace(path)
        if showout:
            self._log_debug("file write:%s" % path)
        return self.sshclient.file_write(path=path, content=content, mode=mode)

    def __repr__(self):
        return "Executor ssh: %s (%s)" % (self.sshclient.addr, self.sshclient.port)

    __str__ = __repr__
