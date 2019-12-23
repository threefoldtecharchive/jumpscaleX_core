from Jumpscale import j

JSBASE = j.baseclasses.object

from .ExecutorBase import ExecutorBase


class ExecutorLocal(ExecutorBase):
    def _init3(self, **kwargs):
        self._cache_expiration = 3600
        self.type = "local"
        self.uid = "localhost"

    def exists(self, path):
        return j.sal.fs.exists(path)

    def execute(self, cmd, die=True, showout=True, timeout=1000, env=None, sudo=False, replace=True, interactive=False):
        """
        @RETURN rc, out, err
        """
        if replace:
            cmd = self._replace(cmd)

        if sudo:
            raise j.exceptions.Base("sudo not supported")

        self._log_debug(cmd)

        return j.core.tools.execute(
            cmd, die=die, showout=showout, timeout=timeout, replace=False, interactive=interactive
        )

    def upload(self, source, dest, dest_prefix="", ignoredir=None, ignorefiles=None, recursive=True):
        """

        :param source:
        :param dest:
        :param dest_prefix:
        :param ignoredir: if None will be [".egg-info",".dist-info"]
        :param recursive:
        :param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache__']
        :param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]
        :return:
        """
        if source == dest:
            raise j.exceptions.Base()
        if dest_prefix != "":
            dest = j.sal.fs.joinPaths(dest_prefix, dest)
        if j.sal.fs.isDir(source):
            j.sal.fs.copyDirTree(
                source,
                dest,
                keepsymlinks=True,
                deletefirst=False,
                overwriteFiles=True,
                ignoredir=ignoredir,
                ignorefiles=ignorefiles,
                rsync=True,
                ssh=False,
                recursive=recursive,
            )
        else:
            j.sal.fs.copyFile(source, dest, overwriteFile=True)
        self._cache.reset()

    def download(self, source, dest, source_prefix=""):
        if source_prefix != "":
            source = j.sal.fs.joinPaths(source_prefix, source)

        if j.sal.fs.isFile(source):
            j.sal.fs.copyFile(source, dest)
        else:
            j.sal.fs.copyDirTree(
                source,
                dest,
                keepsymlinks=True,
                deletefirst=False,
                overwriteFiles=True,
                ignoredir=[".egg-info", ".dist-info"],
                ignorefiles=[".egg-info"],
                rsync=True,
                ssh=False,
            )

    def file_read(self, path):
        return j.sal.fs.readFile(path)

    def file_write(self, path, content, mode=None, owner=None, group=None, append=False, sudo=False, showout=True):
        j.sal.fs.createDir(j.sal.fs.getDirName(path))
        j.sal.fs.writeFile(path, content, append=append)
        if owner is not None or group is not None:
            j.sal.fs.chown(path, owner, group)
        if mode is not None:
            j.sal.fs.chmod(path, mode)
