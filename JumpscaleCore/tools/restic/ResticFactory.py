from Jumpscale import j
from .ResticBackupJob import ResticBackupJob


class ResticFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.tools.restic"

    _CHILDCLASS = ResticBackupJob

    def test(self):
        """
        kosmos 'j.tools.restic.test()'
        :return:
        """

        cl = j.clients.ssh.get(name="explorer")

        j.tools.restic.delete(name="test")
        r = j.tools.restic.new(name="test")

        # @url = jumpscale.restic.instance.1
        # name** = "" (S)
        # secret_ = ""
        # sources = (LO) !jumpscale.restic.instance.source.1
        # dest = (O) !jumpscale.restic.instance.dest.1
        #
        # @url = jumpscale.restic.instance.dest.1
        # backupdir = ""
        # sshclient_name = "" (S)
        #
        # @url = jumpscale.restic.instance.source.1
        # #optional ssh client to do the restic operation on
        # sshclient_name = "" (S)
        # paths = []
        # tag = ""
        # ignoredir = [] (LS)

        j.tools.restic.delete(name="test")
        job = j.tools.restic.get(name="test", sshclient_name="explorer")

        # # backup to subdir
        # s = job.sources.new()
        # s.paths.append("{DIR_CODE}/github/threefoldtech/jumpscaleX_core")
        # s.paths.append("{DIR_CODE}/github/threefoldtech/jumpscaleX_builders")
        # s.tag = "myself"

        s2 = job.sources.new()
        s2.paths.append("{DIR_CODE}/github/threefoldtech/jumpscaleX_core")
        s2.paths.append("{DIR_CODE}/github/threefoldtech/jumpscaleX_builders")
        s2.tag = "remote"
        s2.sshclient_name = "explorer"

        job.secret_ = "1234"
        job.dest.backupdir = "/tmp/backuptest"

        # job.install()

        job.backup()

        job.mount()
