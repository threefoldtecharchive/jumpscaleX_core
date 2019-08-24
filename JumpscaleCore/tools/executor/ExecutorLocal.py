from Jumpscale import j

JSBASE = j.baseclasses.object

from .ExecutorBase import ExecutorBase


class ExecutorLocal(ExecutorBase):

    __jslocation__ = "j.tools.executorLocal"

    def _init(self, **kwargs):
        self._cache_expiration = 3600
        self.type = "local"
        self._id = "localhost"
        self._config_msgpack_path = j.core.tools.text_replace("{DIR_CFG}/executor_local_config.msgpack")
        self._env_on_system_msgpack_path = j.core.tools.text_replace("{DIR_CFG}/executor_local_system.msgpack")

    @property
    def config_msgpack(self):
        path = self._config_msgpack_path
        if not j.sal.fs.exists(path):
            return b""
        else:
            return j.sal.fs.readFile(path, binary=True)

    @config_msgpack.setter
    def config_msgpack(self, value):
        path = self._config_msgpack_path
        j.sal.fs.writeFile(path, value)

    def config_save(self, onsystem=True):
        data = j.data.serializers.msgpack.dumps(self.config)
        if j.data.hash.md5_string(self.config_msgpack) != j.data.hash.md5_string(data):
            # now we know the configuration has been changed
            self._log_debug("config save on: %s" % self)
            self.config_msgpack = data
            self.save()

    @property
    def env_on_system_msgpack(self):
        path = self._env_on_system_msgpack_path
        if not j.sal.fs.exists(path):
            return ""
        else:
            return j.sal.fs.readFile(path, binary=True)

    @env_on_system_msgpack.setter
    def env_on_system_msgpack(self, value):
        path = self._env_on_system_msgpack_path
        j.sal.fs.writeFile(path, value)

    def exists(self, path):
        return j.sal.fs.exists(path)

    def shell(self, cmd=None):
        if cmd:
            j.shell()
        if mosh:
            cmd = "mosh {login}@{addr} -p {port}"
        else:
            cmd = "ssh {login}@{addr} -p {port}"
        cmd = self._replace(cmd)
        j.sal.process.executeWithoutPipe(cmd)

    def kosmos(self, cmd=None):
        j.shell()

    def execute(
        self, cmd, die=True, showout=False, timeout=1000, env=None, sudo=False, replace=True, interactive=False
    ):
        """
        @RETURN rc, out, err
        """
        if replace:
            if env is None:
                env = {}
            env.update(self.env)
            assert self.env != {}
            cmd = self._replace(cmd, args=env)

        if sudo:
            raise j.exceptions.Base("sudo not supported")

        self._log_debug(cmd)

        return j.core.tools.execute(
            cmd, die=die, showout=showout, timeout=timeout, replace=replace, interactive=interactive
        )

    # def executeRaw(self, cmd, die=True, showout=False):
    #     return self.execute(cmd, die=die, showout=showout)

    # def executeInteractive(self, cmds, die=True, checkok=None):
    #     cmds = self.commands_transform(cmds, die, checkok=checkok)
    #     return j.sal.process.executeWithoutPipe(cmds)

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

    # def systemenv_load(self):
    #     """
    #     is dict of all relevant param's on system
    #     """
    #
    #     def getenv():
    #         res = {}
    #         for key, val in os.environ.items():
    #             res[key].upper() = val
    #         return res
    #
    #     homedir = j.core.myenv.config["DIR_HOME"]
    #
    #     # print ("INFO: stateonsystem for local")
    #     res = {}
    #     res["ENV"] = getenv()
    #     res["UNAME"] = (
    #         subprocess.Popen("uname -mnprs", stdout=subprocess.PIPE, shell=True).stdout.read().decode().strip()
    #     )
    #     res["HOSTNAME"] = socket.gethostname()
    #
    #     if "darwin" in sys.platform.lower():
    #         res["OS_TYPE"] = "darwin"
    #     elif "linux" in sys.platform.lower():
    #         res["OS_TYPE"] = "ubuntu"  # dirty hack, will need to do something better, but keep fast
    #     else:
    #         print("need to fix for other types (check executorlocal")
    #         sys.exit(1)
    #
    #     path = "%s/.profile_js" % (homedir)
    #     if os.path.exists(path):
    #         res["bashprofile"] = j.sal.fs.readFile(path)
    #     else:
    #         res["bashprofile"] = ""
    #
    #     if os.path.exists("/root/.iscontainer"):
    #         res["iscontainer"] = True
    #     else:
    #         res["iscontainer"] = False
    #
    #     res["HOME"] = j.core.myenv.config["DIR_HOME"]
    #
    #     self.env_on_system_msgpack = j.data.serializers.msgpack.dumps(res)
    #     self.save()
