from Jumpscale import j

import base64
from .ExecutorInstallers import ExecutorInstallers

JSBASE = j.baseclasses.object


class ExecutorBase(JSBASE):
    def __init__(self, debug=False, checkok=True):
        self.debug = debug
        self.checkok = checkok
        self.type = None

        self._id = None
        self._env = {}
        self.readonly = False
        self.CURDIR = ""

        # self._state = None

        JSBASE.__init__(self)

        self._installer = None

        self._env_on_system = None

        self._init3()

    @property
    def installer(self):
        if not self._installer:
            self._installer = ExecutorInstallers(executor=self)
        return self._installer

    def reset(self):
        self.state_reset()
        self._init3()
        self.save()

    def _init3(self):
        self._config = None
        self._env_on_system = None

    @property
    def config(self):
        if not self._config:
            if self.config_msgpack:
                self._config = j.data.serializers.msgpack.loads(self.config_msgpack)
            else:
                self._config = {}
        return self._config

    def save(self):
        """
        only relevant for ssh
        :return:
        """
        pass

    @property
    def data(self):
        return self.sshclient.data

    def delete(self, path):
        path = self._replace(path)
        cmd = "rm -rf %s" % path
        self.execute(cmd)

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
        if self.type == "ssh":
            content = self.sshclient._replace(content)
        return j.core.tools.text_replace(content=content, args=args, executor=self)

    def dir_ensure(self, path):
        cmd = "mkdir -p %s" % path
        self.execute(cmd, interactive=False)

    def path_isdir(self, path):
        """
        checks if the path is a directory
        :return:
        """
        rc, out, err = self.execute('if [ -d "%s" ] ;then echo DIR ;fi' % path, interactive=False)
        return out.strip() == "DIR"

    def path_isfile(self, path):
        """
        checks if the path is a directory
        :return:
        """
        rc, out, err = self.execute('if [ -f "%s" ] ;then echo FILE ;fi' % path, interactive=False)
        return out.strip() == "FILE"

    @property
    def platformtype(self):
        return j.core.platformtype.get(self)

    def file_read(self, path):
        self._log_debug("file read:%s" % path)
        rc, out, err = self.execute("cat %s" % path, showout=False, interactive=False)
        return out

    def file_write(self, path, content, mode=None, owner=None, group=None, showout=True):
        """
        @param append if append then will add to file
        """
        path = self._replace(path)
        if showout:
            self._log_debug("file write:%s" % path)

        temp = j.sal.fs.getTmpFilePath()
        j.sal.fs.writeFile(filename=temp, contents=content, append=False)
        self.upload(temp, path)
        j.sal.fs.remove(temp)
        cmd = ""
        if mode:
            cmd += "chmod %s %s && " % (mode, path)
        if owner:
            cmd += "chown %s %s && " % (owner, path)
        if group:
            cmd += "chgrp %s %s &&" % (group, path)
        cmd = cmd.strip().strip("&")

        self.execute(cmd, showout=False, script=False, interactive=False)

        return None

    @property
    def uid(self):
        if self._id is None:
            raise j.exceptions.Base("self._id cannot be None")
        return self._id

    def _commands_transform(self, cmds, die=True, checkok=False, env={}, sudo=False, shell=False):
        # print ("TRANSF:%s"%cmds)

        if sudo or shell:
            checkok = False

        multicommand = "\n" in cmds or ";" in cmds

        if shell:
            if "\n" in cmds:
                raise j.exceptions.Base("cannot do shell for multiline scripts")
            else:
                cmds = "bash -c '%s'" % cmds

        pre = ""

        checkok = checkok or self.checkok

        if die:
            # first make sure not already one
            if "set -e" not in cmds:
                # now only do if multicommands
                if multicommand:
                    if self.debug:
                        pre += "set -ex\n"
                    else:
                        pre += "set -e\n"

        if self.CURDIR != "":
            pre += "cd %s\n" % (self.CURDIR)

        if env != {}:
            for key, val in env.items():
                pre += "export %s=%s\n" % (key, val)

        cmds = "%s\n%s" % (pre, cmds)

        if checkok and multicommand:
            if not cmds.endswith("\n"):
                cmds += "\n"
            cmds += "echo '**OK**'"

        if "\n" in cmds:
            cmds = cmds.replace("\n", ";")
            cmds.strip() + "\n"

        cmds = cmds.replace(";;", ";").strip(";")

        if sudo:
            cmds = self.sudo_cmd(cmds)

        self._log_debug(cmds)

        return cmds

    def find(self, path):
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

    # interface to implement by child classes
    def execute(self, *args, **kwargs):
        raise j.exceptions.NotImplemented()

    # def executeRaw(self, cmd, die=True, showout=False):
    #     raise j.exceptions.NotImplemented()

    @property
    def isDebug(self):
        return (
            self.state.configGetFromDict("system", "debug") == "1"
            or self.state.configGetFromDict("system", "debug") == 1
            or self.state.configGetFromDict("system", "debug")
            or self.state.configGetFromDict("system", "debug") == "true"
        )

    @property
    def isContainer(self):
        """
        means we don't work with ssh-agent ...
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
    def isSandbox(self):
        """
        has this env a sandbox?
        """
        if self._isSandbox is None:
            if self.exists("/sandbox"):
                self._isSandbox = True
            else:
                self._isSandbox = False
        return self._isSandbox

    def debug_enable(self):
        self.state.configSetInDictBool("system", "debug", True)
        self.state.configSave()
        self._cache.reset()

    # def _initEnv(self):
    #     """
    #     init the environment of an executor
    #     """
    #
    #     self._env = self.env_on_system["env"]
    #
    #     self.env_on_system
    #
    #     print("INITENV")  # TMP
    #     self.reset()
    #     j.shell()
    #     w
    #
    #     self.config["system"]["container"] = self.env_on_system["iscontainer"]
    #
    #     if self.isBuildEnv:
    #         # ONLY RELEVANT FOR BUILDING PYTHON, needs to check what needs to be done (kristof) #TODO:
    #         j.shell()
    #
    #     else:
    #         out = ""
    #         for key, val in self.dir_paths.items():
    #             out += "mkdir -p %s\n" % val
    #         self.execute(out, sudo=True, showout=False,interactive=False)
    #
    #     self._cache.reset()
    #
    #     self.config["system"]["executor"] = True
    #     self.config["DIRS"]["HOMEDIR"] = self.env_on_system["HOME"]
    #     self.state.configSave()
    #
    #     if "cfg_state" in self.env_on_system:
    #         self.state._state = self.env_on_system["cfg_state"]
    #
    #     self._log_debug("initenv done on executor base")

    @property
    def cache(self):
        if self._cache is None:
            self._cache = j.core.cache.get("executor" + self.uid, reset=True, expiration=600)  # 10 min
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

    @property
    def env_on_system(self):
        if not self._env_on_system:
            if not self.env_on_system_msgpack:
                self.systemenv_load()
            self._env_on_system = j.data.serializers.msgpack.loads(self.env_on_system_msgpack)
        return self._env_on_system

    @property
    def env(self):
        return self.env_on_system["ENV"]

    @property
    def state(self):
        if "state" not in self.config:
            self.config["state"] = {}
        return self.config["state"]

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

    def systemenv_load(self):
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
        cat /sandbox/cfg/jumpscale_config.msgpack 2>/dev/null || echo ""
        echo --TEXT--

        echo "BASHPROFILE = --TEXT--"
        cat $HOME/.profile_js 2>/dev/null || echo ""
        echo --TEXT--

        echo "ENV = --TEXT--"
        export
        echo --TEXT--
        """
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

        if res["CFG_JUMPSCALE"].strip() != "":
            rconfig = j.core.tools.config_load(content=res["CFG_JUMPSCALE"])
            res["CFG_JUMPSCALE"] = rconfig
        else:
            res["CFG_JUMPSCALE"] = {}

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

        def get_cfg(name, default):
            name = name.upper()
            if "CFG_JUMPSCALE" in res and name in res["CFG_JUMPSCALE"]:
                self.config[name] = res["CFG_JUMPSCALE"]
                return
            if name not in self.config:
                self.config[name] = default

        get_cfg("DIR_HOME", res["ENV"]["HOME"])
        get_cfg("DIR_BASE", "/sandbox")
        get_cfg("DIR_CFG", "/sandbox/cfg")
        get_cfg("DIR_TEMP", "/tmp")
        get_cfg("DIR_VAR", "/sandbox/var")
        get_cfg("DIR_CODE", "/sandbox/code")
        get_cfg("DIR_BIN", "/usr/local/bin")

        self.env_on_system_msgpack = j.data.serializers.msgpack.dumps(res)
        self.save()

    def test(self):

        """
        kosmos 'j.tools.executor.local.test()'
        :return:
        """
        ex = self

        ex.reset()

        assert ex.state == {}
        assert ex.env_on_system_msgpack == b""
        assert ex.config_msgpack == b""

        rc, out, err = ex.execute("ls /")
        assert rc == 0
        assert err == ""
        assert out.endswith("\n")

        ex.state_set("bla")
        assert ex.state == {"bla": None}
        assert ex.state_exists("bla")
        assert ex.state_exists("blabla") == False
        assert ex.state_get("bla") == None
        ex.state_reset()
        assert ex.state_exists("bla") == False
        assert ex.state == {}
        ex.state_set("bla", 1)
        assert ex.state == {"bla": 1}

        e = ex.env_on_system

        assert e["HOME"] == j.core.myenv.config["DIR_HOME"]

        ex.file_write("/tmp/1re", "a")
        assert ex.file_read("/tmp/1re").strip() == "a"

        assert ex.path_isdir("/tmp")
        assert ex.path_isfile("/tmp") == False
        assert ex.path_isfile("/tmp/1re")

        path = ex.download("/tmp/1re", "/tmp/something.txt")
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

        j.sal.fs.remove("/tmp/8889")

        ex.download("/tmp/8888", "/tmp/8889")

        r2 = j.sal.fs.listFilesAndDirsInDir("/tmp/8889")
        r2.sort()
        assert r2 == ["/tmp/8889/1.txt", "/tmp/8889/2.txt", "/tmp/8889/5", "/tmp/8889/5/3.txt"]

        ex.delete("/tmp/8888")
        r2 = ex.find("/tmp/8888")
        assert r2 == []

        j.sal.fs.remove("/tmp/8888")
        j.sal.fs.remove("/tmp/8889")

        ex.reset()
        assert ex.state == {}
        assert ex.env_on_system_msgpack == b""
        assert ex.config_msgpack == b""

        # test that it does not do repeating thing & cache works
        for i in range(1000):
            ptype = self.platformtype

        for i in range(1000):
            env = self.env

        self._log_info("TEST for executor done")
