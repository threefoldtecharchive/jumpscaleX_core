from Jumpscale import j
from .ExecutorInstallers import ExecutorInstallers


class ExecutorBase(j.baseclasses.object_config):

    _SCHEMATEXT = """
        @url = jumpscale.executor.1
        name** = ""
        stdout = True (B)
        debug = True (B)
        readonly = False (B)
        type = "local,ssh,corex,serial" (E)
        connection_name = "" (S)
        timeout = 60
        #configuration information
        config = {} (DICT)
        #used to measure e.g. progress
        state =  {} (DICT)
        uid = ""
        info = (O) !jumpscale.executor.info.1

        @url = jumpscale.executor.info.1
        issandbox = (B)
        issandbox_bin = (B)
        uname = ""
        hostname = ""
        ostype = "unknown,local,darwin,ubuntu" (E)
        cfg_jumpscale = (DICT)
        env = (DICT)

        """

    def _init(self, **kwargs):
        self._autosave = False
        self._cache_expiration = 3600
        self._installer = None
        self._bash = None
        self._init3(**kwargs)
        if not self.info.uname:
            self.load()

    @property
    def env_on_system(self):
        return self.info.env

    def load(self, save=True):
        eos = self._env_on_system
        self.info.issandbox = eos.pop("ISSANDBOX")
        self.info.issandbox_bin = eos.pop("ISSANDBOX_BIN")
        self.info.uname = eos.pop("UNAME")
        self.info.hostname = eos.pop("HOSTNAME")
        self.info.ostype = eos.pop("OS_TYPE")
        self.info.cfg_jumpscale = eos.pop("CFG_JUMPSCALE")
        self.info.env = eos.pop("ENV")
        self.info.env["UNAME"] = self.info.uname
        self.info.env["HOSTNAME"] = self.info.hostname
        self.info.env["OS_TYPE"] = str(self.info.ostype)
        if save:
            self.save()

    def download(self, source, dest=None, ignoredir=None, ignorefiles=None, recursive=True):
        raise j.exceptions.NotImplemented()

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
        raise j.exceptions.NotImplemented()

    @property
    def installer(self):
        if not self._installer:
            self._installer = ExecutorInstallers(executor=self)
        return self._installer

    @property
    def bash(self):
        if not self._bash:
            self._bash = j.tools.bash.get(path=None, profile_name=None, executor=self)
        return self._bash

    @property
    def profile(self):
        return self.bash.profile

    def delete(self, path):
        self.execute("rm -rf %s" % path)

    def exists(self, path):
        path = self._replace(path)
        rc, _, _ = self.execute("test -e %s" % path, die=False, showout=False)
        if rc > 0:
            return False
        else:
            return True

    def _replace(self, content, args=None):
        """
        args will be substitued to .format(...) string function https://docs.python.org/3/library/string.html#formatspec
        MyEnv.config will also be given to the format function

        content example:

        "{name!s:>10} {val} {n:<10.2f}"  #floating point rounded to 2 decimals

        performance is +100k per sec
        """
        res = j.core.tools.text_replace(content=content, args=args, executor=self)
        if "{" in res:
            j.shell()
        return res

    def dir_ensure(self, path):
        path = self._replace(path)
        cmd = "mkdir -p %s" % path
        self.execute(cmd, interactive=False)

    def path_isdir(self, path):
        """
        checks if the path is a directory
        :return:
        """
        path = self._replace(path)
        rc, out, err = self.execute('if [ -d "%s" ] ;then echo DIR ;fi' % path, interactive=False)
        return out.strip() == "DIR"

    def path_isfile(self, path):
        """
        checks if the path is a directory
        :return:
        """
        path = self._replace(path)
        rc, out, err = self.execute('if [ -f "%s" ] ;then echo FILE ;fi' % path, interactive=False)
        return out.strip() == "FILE"

    @property
    def platformtype(self):
        return j.core.platformtype.get(self)

    @property
    def wireguard_server(self):
        if not self._wireguard:
            from Jumpscale.core.InstallTools import WireGuardServer

            self._wireguard = WireGuardServer(self.addr, port=self.port)
        return self._wireguard

    def package_install(self, name):
        """
        use system installer to install a component
        :return:
        """
        if str(self.platformtype).startswith("darwin64"):
            cmd = "brew install %s" % name
        elif str(self.platformtype).startswith("ubuntu"):
            cmd = "apt install %s" % name
        else:
            raise j.exceptions.NotImplemented("only ubuntu & osx supported")
        self.execute(cmd)

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
        python=None,
        jumpscale=None,
        debug=False,
        cmd_process=True,
    ):
        """
        @RETURN rc, out, err
        """
        if env or sudo:
            raise j.exceptions.NotFound("Not implemented for ssh executor")
            return self.execute(cmd)
        script_path = None
        if replace:
            cmd = self._replace(cmd)
        if cmd_process:
            cmd, script_path = self._cmd_process(
                cmd=cmd,
                python=python,
                jumpscale=jumpscale,
                die=die,
                env=env,
                sudo=sudo,
                interactive=interactive,
                debug=debug,
            )
        res = self._execute_cmd(cmd=cmd, interactive=interactive, showout=showout, die=die, timeout=timeout)
        if script_path:
            self.delete(script_path)
        return res

    def find(self, path):
        path = self._replace(path)
        rc, out, err = self.execute("find %s" % path, die=False, interactive=False)
        if rc > 0:
            if err.lower().find("no such file") != -1:
                return []
            raise j.exceptions.Base("could not find:%s \n%s" % (path, err))
        res = []
        for line in out.split("\n"):
            if line.strip() == path:
                continue
            if line.strip() == "":
                continue
            res.append(line)
        res.sort()
        return res

    def kosmos(self, cmd=None):
        if not cmd:
            cmd = self._replace("source {DIR_BASE}/env.sh && kosmos")
        else:
            cmd = self._cmd_process(cmd=cmd, interactive=True, jumpscale=True)
        return self.shell(cmd=cmd, interactive=True, cmdprocess=False)

    def _cmd_process(
        self, cmd, python=None, jumpscale=None, die=True, env={}, sudo=None, interactive=False, debug=False
    ):
        """
        if file then will read
        if \n in cmd then will treat as script
        if ; in cmd then will convert to script
        if script will upload as file

        :param cmd:
        :param interactive: means we will run as interactive in a shell, for python always the case

        :return:
        """
        assert sudo is None or sudo is False  # not implemented yet
        if env is None:
            env = {}

        if j.sal.fs.exists(cmd):
            ext = j.sal.fs.getFileExtension(cmd).lower()
            cmd = j.sal.fs.readFile(cmd)
            if python is None and jumpscale is None:
                if ext == "py":
                    python = True

        script = None
        # if ";" in cmd and not "\n" in cmd:
        #     cmd = "\n".join(cmd.split(";"))

        if "\n" in cmd or python or jumpscale:
            script = cmd

        dest = None
        if script:
            if python or jumpscale:
                dest = "/tmp/script_%s.py" % j.data.randomnames.hostname()

                if jumpscale:
                    script = self._script_process_jumpscale(script=script, die=die, env=env, debug=debug)
                    cmd = self._replace("source {DIR_BASE}/env.sh && kosmos %s" % dest)
                else:
                    script = self._script_process_python(script, env=env)
                    cmd = self._replace("source {DIR_BASE}/env.sh && python3 %s" % dest)
            else:
                dest = "/tmp/script_%s.sh" % j.data.randomnames.hostname()
                if die:
                    cmd = "bash -ex %s" % dest
                else:
                    cmd = "bash -x %s" % dest
                script = self._script_process_bash(script, die=die, env=env, debug=debug)

            self.file_write(dest, script)

        return cmd, dest

    def _script_process_jumpscale(self, script, env={}, debug=False):
        pre = ""

        if "from Jumpscale import j" not in script:
            # now only do if multicommands
            pre += "from Jumpscale import j\n"

        if debug:
            pre += "j.application.debug = True\n"  # TODO: is this correct

        if pre:
            script = "%s\n%s" % (pre, script)

        script = self._script_process_python(script, env=env)

        return script

    def _script_process_python(self, script, env={}):
        pre = ""

        if env != {}:
            for key, val in env.items():
                pre += "%s = %s\n" % (key, val)

        if pre:
            script = "%s\n%s" % (pre, script)

        return script

    def _script_process_bash(self, script, die=True, env={}, sudo=False, debug=False):

        pre = ""

        if die:
            # first make sure not already one
            if "set -e" not in script:
                # now only do if multicommands
                if self.debug:
                    pre += "set -ex\n"
                else:
                    pre += "set -e\n"

        if env != {}:
            for key, val in env.items():
                pre += "export %s=%s\n" % (key, val)

        if pre:
            script = "%s\n%s" % (pre, script)

        # if sudo:
        #     script = self.sudo_cmd(script)

        return script

    def shell(self, cmd=None, interactive=True, cmdprocess=True):
        if cmdprocess:
            cmd = self._cmd_process(cmd=cmd, interactive=interactive)
        self.execute(cmd, interactive=True)
        # j.sal.process.executeWithoutPipe(cmd)

    def cmd_installed(self, cmd):
        rc, _, _ = self.execute("which %s" % cmd, die=False)
        if rc:
            return False
        else:
            return True

    @property
    def container_check(self):
        """
        return True if we are in a container
        """

        if not "IN_DOCKER" in self.config:
            rc, out, _ = self.execute("cat /proc/1/cgroup", die=False, showout=False, interactive=False)
            if rc == 0 and out.find("/docker/") != -1:
                self.config["IN_DOCKER"] = True
            else:
                self.config["IN_DOCKER"] = False
            self.save()

        return j.data.types.bool.clean(self.config["IN_DOCKER"])

    @property
    def sandbox_check(self):
        """
        has this env a sandbox?
        """
        if self._sandbox_check is None:
            if self.exists(self._replace("{DIR_BASE}")):
                self._sandbox_check = True
            else:
                self._sandbox_check = False
        return self._sandbox_check

    @property
    def cache(self):
        if self._cache is None:
            self._cache = j.core.cache.get("executor_" + self.name, reset=True, expiration=600)  # 10 min
        return self._cache

    # def sudo_cmd(self, command):
    #
    #     if "\n" in command:
    #         raise j.exceptions.Base("cannot do sudo when multiline script:%s" % command)
    #
    #     if hasattr(self, "sshclient"):
    #         login = self.sshclient.config.data["login"]
    #         passwd = self.sshclient.config.data["passwd_"]
    #     else:
    #         login = getattr(self, "login", "")
    #         passwd = getattr(self, "passwd", "")
    #
    #     if "darwin" in self.platformtype.osname:
    #         return command
    #     if login == "root":
    #         return command
    #
    #     passwd = passwd or "''"
    #
    #     cmd = "echo %s | sudo -H -SE -p '' bash -c \"%s\"" % (passwd, command.replace('"', '\\"'))
    #     return cmd

    def state_exists(self, key):
        key = j.core.text.strip_to_ascii_dense(key)
        return key in self.state

    def state_set(self, key, val=None, save=True):
        key = j.core.text.strip_to_ascii_dense(key)
        if key not in self.state or self.state[key] != val:
            self.state[key] = val
            self.save()

    def state_get(self, key, default_val=None):
        key = j.core.text.strip_to_ascii_dense(key)
        if key not in self.state:
            if default_val:
                self.state[key] = default_val
                return default_val
            else:
                return None
        else:
            return self.state[key]

    def state_delete(self, key):
        key = j.core.text.strip_to_ascii_dense(key)
        if key in self.state:
            self.state.pop(key)

    def state_reset(self):
        self.config["state"] = {}

    @property
    def _env_on_system(self):
        """
        get relevant information from remote system e.g. hostname, env variables, ...
        :return:
        """
        C = """
        set +ex
        ls "/sandbox"  > /dev/null 2>&1 && echo 'ISSANDBOX = 1' || echo 'ISSANDBOX = 0'

        ls "/sandbox/bin/python3"  > /dev/null 2>&1 && echo 'ISSANDBOX_BIN = 1' || echo 'ISSANDBOX_BIN = 0'
        echo UNAME = \""$(uname -mnprs)"\"
        echo "HOME = $HOME"
        echo HOSTNAME = "$(hostname)"
        if [[ "$(uname -s)" == "Darwin" ]]; then
            echo OS_TYPE = "darwin"
        else
            echo OS_TYPE = "ubuntu"
        fi

        # lsmod > /dev/null 2>&1|grep vboxdrv |grep -v grep  > /dev/null 2>&1 && echo 'VBOXDRV=1' || echo 'VBOXDRV=0'

        # #OS
        # apt-get -v > /dev/null 2>&1 && echo 'OS_TYPE="ubuntu"'
        # test -f /etc/arch-release > /dev/null 2>&1 && echo 'OS_TYPE="arch"'
        # test -f /etc/redhat-release > /dev/null 2>&1 && echo 'OS_TYPE="redhat"'
        # apk -v > /dev/null 2>&1 && echo 'OS_TYPE="alpine"'
        # brew -v > /dev/null 2>&1 && echo 'OS_TYPE="darwin"'
        # opkg -v > /dev/null 2>&1 && echo 'OS_TYPE="LEDE"'
        # cat /etc/os-release | grep "VERSION_ID"
        #

        echo "CFG_JUMPSCALE = --TEXT--"
        cat /sandbox/cfg/jumpscale_config.toml 2>/dev/null || echo ""
        echo --TEXT--

        # echo "BASHPROFILE = --TEXT--"
        # cat $HOME/.profile_js 2>/dev/null || echo ""
        # echo --TEXT--

        echo "ENV = --TEXT--"
        export
        echo --TEXT--
        """
        C = j.core.tools.text_strip(C)
        rc, out, err = self.execute(C, showout=False, interactive=False, replace=False)
        res = {}
        state = ""
        for line in out.split("\n"):
            if line.find("--TEXT--") != -1 and line.find("=") != -1:
                varname = line.split("=")[0].strip().lower()
                state = "TEXT"
                txt = ""
                continue

            if state == "TEXT":
                if line.strip() == "--TEXT--":
                    res[varname.upper()] = txt
                    state = ""
                    continue
                else:
                    txt += line + "\n"
                    continue

            if "=" in line:
                varname, val = line.split("=", 1)
                varname = varname.strip().lower()
                val = str(val).strip().strip('"')
                if val.lower() in ["1", "true"]:
                    val = True
                elif val.lower() in ["0", "false"]:
                    val = False
                else:
                    try:
                        val = int(val)
                    except BaseException:
                        pass
                res[varname.upper()] = val

        if not self.type == "local":
            config = j.core.tools.config_load(content=res["CFG_JUMPSCALE"])
            if "DIR_BASE" not in config:
                config["DIR_BASE"] = "/sandbox"
            if "DIR_HOME" not in config:
                config["DIR_HOME"] = res["HOME"]
            if "DIR_CFG" not in config:
                config["DIR_CFG"] = "%s/cfg" % config["DIR_BASE"]
            rconfig = j.core.myenv.config_default_get(config=config)
            res["CFG_JUMPSCALE"] = rconfig
        else:
            res["CFG_JUMPSCALE"] = j.core.myenv.config

        envdict = {}
        for line in res["ENV"].split("\n"):
            line = line.replace("declare -x", "")
            line = line.strip()
            if line.strip() == "":
                continue
            if "=" in line:
                pname, pval = line.split("=", 1)
                pval = pval.strip("'").strip('"')
                envdict[pname.strip().upper()] = pval.strip()

        res["ENV"] = envdict

        # def get_cfg(name, default):
        #     name = name.upper()
        #     if "CFG_JUMPSCALE" in res and name in res["CFG_JUMPSCALE"]:
        #         self.config[name] = res["CFG_JUMPSCALE"]
        #         return
        #     if name not in self.config:
        #         self.config[name] = default
        #
        # if self.type != "local":
        #     get_cfg("DIR_HOME", res["ENV"]["HOME"])
        #     get_cfg("DIR_BASE", "/sandbox")
        #     get_cfg("DIR_CFG", "/sandbox/cfg")
        #     get_cfg("DIR_TEMP", "/tmp")
        #     get_cfg("DIR_VAR", "/sandbox/var")
        #     get_cfg("DIR_CODE", "/sandbox/code")
        #     get_cfg("DIR_BIN", "/usr/local/bin")

        return res

    def state_reset(self):
        self.state = {}

    def reset(self):
        self.state_reset()
        self.config = {}
        self.info.uname = ""
        self.info.hostname = ""
        self.info.cfg_jumpscale = {}
        self.info.env = {}
        self.info.ostype = "unknown"
        self.load()

    def test(self):

        """
        kosmos 'j.tools.executor.local.test()'
        :return:
        """
        ex = self

        ex.reset()

        assert ex.state == {}
        assert ex.config == {}

        rc, out, err = ex.execute("ls /")
        assert rc == 0
        assert err == ""
        assert out.endswith("\n")

        ex.state_set("bla")
        assert ex.state == {"bla": None}
        assert ex.state_exists("bla")
        assert ex.state_exists("blabla") is False
        assert ex.state_get("bla") is None
        ex.state_reset()
        assert ex.state_exists("bla") is False
        assert ex.state == {}
        ex.state_set("bla", 1)
        assert ex.state == {"bla": 1}

        if self.type == "local":
            assert self.info.cfg_jumpscale["DIR_HOME"] == j.core.myenv.config["DIR_HOME"]
        else:
            assert self.info.cfg_jumpscale["DIR_HOME"]

        ex.file_write("/tmp/1re", "a")
        assert ex.file_read("/tmp/1re").strip() == "a"

        ex.delete("/tmp/adir")
        ex.dir_ensure("/tmp/adir")
        assert ex.exists("/tmp/adir")
        # see if it creates intermediate non existing dir
        ex.file_write("/tmp/adir/notexist/a.txt", "aa")
        assert ex.exists("/tmp/adir/notexist/a.txt")
        ex.delete("/tmp/adir")
        assert ex.exists("/tmp/adir") is False

        err = False
        try:
            ex.execute("ls /tmp/sssss")
        except:
            err = True
        assert err

        assert ex.path_isdir("/tmp")
        assert ex.path_isfile("/tmp") is False
        assert ex.path_isfile("/tmp/1re")

        path = ex.download("/tmp/1re", "/tmp/something.txt")
        assert j.sal.fs.readFile("/tmp/something.txt").strip() == "a"
        path = ex.upload("/tmp/something.txt", "/tmp/2re")

        assert ex.file_read("/tmp/2re").strip() == "a"

        assert j.sal.fs.readFile("/tmp/something.txt").strip() == "a"
        j.sal.fs.remove("/tmp/something.txt")

        j.sal.fs.createDir("/tmp/8888")
        j.sal.fs.createDir("/tmp/8888/5")
        j.sal.fs.writeFile("/tmp/8888/1.txt", "a")
        j.sal.fs.writeFile("/tmp/8888/2.txt", "a")
        j.sal.fs.writeFile("/tmp/8888/5/3.txt", "a")

        path = ex.upload("/tmp/8888", "/tmp/8889")

        ex.delete("/tmp/2re")
        ex.delete("/tmp/1re")

        r = ex.find("/tmp/8889")
        assert r == ["/tmp/8889/1.txt", "/tmp/8889/2.txt", "/tmp/8889/5", "/tmp/8889/5/3.txt"]

        ex.download("/tmp/8889", "/tmp/8890")
        j.sal.fs.remove("/tmp/8889")

        r2 = j.sal.fs.listFilesAndDirsInDir("/tmp/8890")
        r2.sort()
        assert r2 == ["/tmp/8890/1.txt", "/tmp/8890/2.txt", "/tmp/8890/5", "/tmp/8890/5/3.txt"]

        ex.delete("/tmp/8890")
        r2 = ex.find("/tmp/8890")
        assert r2 == []

        j.sal.fs.remove("/tmp/8890")

        ex.reset()
        assert ex.state == {}

        # test that it does not do repeating thing & cache works
        for i in range(1000):
            ptype = self.platformtype

        self._log_info("TEST for executor done")
