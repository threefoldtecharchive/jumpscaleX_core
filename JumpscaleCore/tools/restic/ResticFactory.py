from Jumpscale import j
from .ResticBackupJob import ResticBackupJob

skip = j.baseclasses.testtools._skip


class ResticFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.tools.restic"

    _CHILDCLASS = ResticBackupJob

    def backup(self, mount=False):
        """
        kosmos 'j.tools.restic.backup()'

        will make a full blown backup of all relevant data in threebot
        :return:
        """

        j.data.bcdb.stop()

        b = self._default_job_get()

        b.install()
        b.backup()

        if mount:
            b.mount()

    def _default_job_get(self):
        b = self.get(name="threebot")

        # @url = jumpscale.restic.instance.1
        # name** = "" (S)
        # secret_ = ""
        # sources = (LO) !jumpscale.restic.instance.source.1
        # dest = (O) !jumpscale.restic.instance.dest.1
        #
        # @url = jumpscale.restic.instance.dest.1
        # sshclient_name = "" (S)
        # backupdir = ""
        #
        # @url = jumpscale.restic.instance.source.1
        # #optional ssh client to do the restic operation on
        # sshclient_name = "" (S)
        # paths = [] (LS)
        # tag = ""
        # ignoredir = [] (LS)

        b.secret_ = j.core.myenv.adminsecret
        b.sources = []
        s = b.sources.new()
        s.paths.append("/sandbox/cfg")
        s.paths.append("/sandbox/var/bcdb")
        s.paths.append("/sandbox/var/bcdb_exports")
        s.paths.append("/sandbox/var/zdb")

        # j.debug()
        b.dest.backupdir = "/root/backups"

        return b

    def mount(self):
        """
        kosmos 'j.tools.restic.mount()'
        """

        b = self._default_job_get()
        b.mount()

    def test(self):
        """
        kosmos 'j.tools.restic.test()'
        :return:
        """
        if not j.sal.fs.exists("{DIR_BIN}/restic"):
            j.builders.storage.restic.install(reset=True)
        j.tools.restic.delete(name="test_restic")
        job = j.tools.restic.get(name="test_restic")
        job.secret_ = "1234"
        job.dest.backupdir = "/tmp/backuptest"
        j.sal.fs.remove("/tmp/backuptest/*")
        j.sal.fs.remove("/tmp/backuptest")

        # # backup to local dir
        s = job.sources.new()
        s.paths.append("{DIR_CODE}/github/threefoldtech/jumpscaleX_core")
        s.paths.append("{DIR_CODE}/github/threefoldtech/jumpscaleX_builders")
        s.tag = "myself"

        job.backup()
        print("TEST OK")
