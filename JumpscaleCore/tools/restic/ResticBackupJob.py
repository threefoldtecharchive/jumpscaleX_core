from Jumpscale import j


class ResticBase(j.baseclasses.object):
    @property
    def sshclient(self):
        if self._sshclient_name:
            return j.clients.ssh.get(name=self._sshclient_name)
        else:
            raise j.exceptions.Input("sshclient not specified")

    @property
    def executor(self):
        if self._sshclient_name:
            return self.sshclient.executor
        else:
            return j.tools.executor.local

    def install(self):
        if not self.executor.cmd_installed("restic"):
            self.executor.install("restic")

    def _cmd_execute(self, cmd):
        if not self.secret_:
            raise j.exceptions.Input("please specify restic secret_ ")
        cmd = "export RESTIC_PASSWORD='%s';restic %s" % (self.secret_, cmd)
        return self.executor.execute(cmd)


class ResticSource(ResticBase):
    def _init(self, job, source):
        self.job = job
        self.source = source
        self.dest = job.dest
        self.secret_ = self.job.secret_

    @property
    def _sshclient_name(self):
        return self.source.sshclient_name

    def backup(self, reset=False, port=None):
        """
        """
        for path in self.source.paths:
            path = self.executor._replace(path)
            assert len(path) > 2
            IGNOREDIR = [".git", ".github"]
            if self.source.tag:
                tag = "--tag %s" % self.source.tag
            else:
                tag = ""
            if port:
                self._cmd_execute(f" backup -r 'rest:http://localhost:{port}' {tag} '{path}'")
            else:
                self._cmd_execute(f" -r '{self.dest.backupdir}' backup {tag} '{path}'")


class ResticBackupJob(ResticBase, j.baseclasses.object_config):

    """
    :param sshclient_name: name as used in j.clients.ssh
    :param source: specified as
        e.g.  "{DIR_CODE}/github/threefoldtech/0-robot:{DIR_TEMP}/0-robot"

    """

    _SCHEMATEXT = """
        @url = jumpscale.restic.instance.1
        name** = "" (S)
        secret_ = ""
        sources = (LO) !jumpscale.restic.instance.source.1
        dest = (O) !jumpscale.restic.instance.dest.1

        @url = jumpscale.restic.instance.dest.1
        sshclient_name = "" (S)
        backupdir = ""

        @url = jumpscale.restic.instance.source.1
        #optional ssh client to do the restic operation on
        sshclient_name = "" (S)
        paths = [] (LS)
        tag = ""
        ignoredir = [] (LS)

        """

    @property
    def _sshclient_name(self):
        return self.dest.sshclient_name

    def _load(self):
        if not self.dest.backupdir:
            self.dest.backupdir = "/root/backups"
        self.init_backup_dir()
        assert not self.sshclient_name  # not implement yet

    def init_backup_dir(self, reset=False):
        if reset:
            self.executor.execute(f"rm -rf {self.dest.backupdir}")
        if reset or not self.executor.exists(self.dest.backupdir):
            self.executor.execute(f"mkdir -p {self.dest.backupdir}")
            self._cmd_execute("init --repo %s" % self.dest.backupdir)

    def install(self):
        self._load()
        for source in self.sources:
            rs = ResticSource(job=self, source=source)
            rs.install()

    def server_rest_start(self):
        cmd = j.servers.startupcmd.get(name="rest-server")
        cmd.cmd_start = "rest-server --path %s --append-only --no-auth --listen localhost:8111" % self.dest.backupdir
        cmd.ports = [8111]
        cmd.timeout = 20
        cmd.process_strings = ["rest-server"]
        cmd.executor = "tmux"
        cmd.start()

    def backup(self):
        self.init_backup_dir()
        for source in self.sources:
            rs = ResticSource(job=self, source=source)
            if rs._sshclient_name and not self._sshclient_name:
                # means we are on localhost & other is remote ssh, prob we're behind nat
                self.server_rest_start()
                rs.sshclient.portforward_to_remote(8112, 8111)
                rs.backup(port=8112)
            elif self._sshclient_name and rs._sshclient_name and self._sshclient_name == rs._sshclient_name:
                rs.backup()  # is a local backup but over ssh
            elif not self._sshclient_name and not rs._sshclient_name:
                # local backup
                rs.backup()
            else:
                raise j.exceptions.Base("not supported yet")

    def mount(self, mountpath="/tmp/1"):
        cmd = f"rm -rf {mountpath};restic -r {self.dest.backupdir} mount {mountpath}"
        self.executor.execute(cmd)
