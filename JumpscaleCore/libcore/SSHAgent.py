import os
import random
import shutil
import sys
from Tools import Tools

import pickle


class SSHAgentKeyError(Exception):
    pass


class SSHAgent:
    _myenv = None

    def __init__(self):
        self._inited = False
        self._default_key = None
        self.autostart = True
        self._DockerFactory = None
        self.reset()

    def DockerFactory(self):
        if not self._DockerFactory:
            from Docker import DockerFactory

            self._DockerFactory = DockerFactory
        return self._DockerFactory

    @property
    def ssh_socket_path(self):

        if "SSH_AUTH_SOCK" in os.environ:
            return os.environ["SSH_AUTH_SOCK"]

        socketpath = Tools.text_replace("{DIR_VAR}/sshagent_socket")
        os.environ["SSH_AUTH_SOCK"] = socketpath
        return socketpath

    @property
    def myenv(self):
        if not self._myenv:
            from MyEnv import MyEnv

            self._myenv = MyEnv()
        return self._myenv

    def _key_name_get(self, name=None):

        if not name:
            if self.myenv.config["SSH_KEY_DEFAULT"]:
                name = self.myenv.config["SSH_KEY_DEFAULT"]
            elif self.myenv.interactive:
                name = Tools.ask_string("give name for your sshkey,default='default'")
                if not name:
                    name = "default"
            else:
                name = "default"
        return name

    def key_generate(self, name=None, passphrase=None, reset=False):
        """
        Generate ssh key

        :param reset: if True, then delete old ssh key from dir, defaults to False
        :type reset: bool, optional
        """
        Tools.log("generate ssh key")
        name = self._key_name_get(name)

        if not passphrase:
            if self.myenv.interactive:
                passphrase = Tools.ask_password("passphrase for ssh key to generate (empty=None)", emptyok=True)

        path = Tools.text_replace("{DIR_HOME}/.ssh/%s" % name)
        Tools.dir_ensure("{DIR_HOME}/.ssh")

        if reset:
            Tools.delete("%s" % path)
            Tools.delete("%s.pub" % path)

        if not Tools.exists(path) or reset:
            if passphrase:
                cmd = f'ssh-keygen -t rsa -f {path} -N "{passphrase}" -C {name}'
            else:
                cmd = f"ssh-keygen -t rsa -f {path} -C {name}"
            Tools.execute(cmd, timeout=10)

            Tools.log("load generated sshkey: %s" % path)

        return path

    @property
    def key_default_name(self):
        """

        kosmos 'print(j.core.myenv.sshagent.key_default_name)'

        checks if it can find the default key for ssh-agent, if not will ask
        :return:
        """
        return self.init()

    def _ssh_keys_names_on_fs(self, hdir=None):
        DIR_HOME = self.myenv.config["DIR_HOME"]
        if not hdir:
            hdir = f"{DIR_HOME}/.ssh"
        choices = []
        if Tools.exists(hdir):
            for item in os.listdir(hdir):
                item2 = item.lower()
                if not (
                    item.startswith(".")
                    or item2.endswith((".pub", ".backup", ".toml", ".old"))
                    or item in ["known_hosts", "config", "authorized_keys"]
                ):
                    choices.append(item)
        return choices

    def init(self):

        DIR_HOME = self.myenv.config["DIR_HOME"]
        DIR_BASE = self.myenv.config["DIR_BASE"]

        def ask_key(key_names):
            if len(key_names) == 1:
                name = key_names[0]
            elif len(key_names) == 0:
                return None
            else:
                name = Tools.ask_choices("Which is your default sshkey to use", key_names)
            return name

        self._keys  # will fetch the keys if not possible will show error

        if "SSH_KEY_DEFAULT" in self.myenv.config and self.myenv.config["SSH_KEY_DEFAULT"]:
            sshkey = self.myenv.config["SSH_KEY_DEFAULT"]
            if not sshkey in self.key_names:
                res = self.key_load(name=sshkey, die=False)
                if res == None:
                    return None
                sshkey = None
                self.myenv.config["SSH_KEY_DEFAULT"] = ""
        else:
            sshkey = None

        # check if more than 1 key in ssh-agent
        if not sshkey:
            sshkey = ask_key(self.key_names)

        # no ssh key lets see if there are ssh keys in the default .ssh dir
        if not sshkey:
            choices = self._ssh_keys_names_on_fs()
            if len(choices) > 0:
                sshkey = ask_key(choices)

        myhost_sshkey_dir = f"{DIR_BASE}/myhost/sshkey"
        if not sshkey and Tools.exists(myhost_sshkey_dir):
            # lets check if there is a key in the myhost dir
            res = os.listdir(myhost_sshkey_dir)
            if len(res) == 1:
                sshkey = res[0]
                myhost_sshkey_path = f"{myhost_sshkey_dir}/{sshkey}"
                sshkeypath = f"{DIR_HOME}/.ssh/{sshkey}"
                shutil.copyfile(myhost_sshkey_path, sshkeypath)

        # if no key yet, need to generate
        if not sshkey:
            if Tools.ask_yes_no("ok to generate a default ssh key?"):
                sshkey = self._key_name_get()
                sshkeypath = self.key_generate(name=sshkey)
            else:
                print("CANNOT CONTINUE, PLEASE GENERATE AN SSHKEY AND RESTART")
                sys.exit(1)

        if not sshkey in self.key_names:
            if self.DockerFactory.indocker():
                raise Tools.exceptions.Base("sshkey should be passed forward by means of SSHAgent")
            self.key_load(name=sshkey)

        if not sshkey in self.key_names:
            raise Tools.exceptions.Input(f"SSH key '{sshkey}' was not loaded, should have been by now.")

        myhost_sshkey_path = f"{myhost_sshkey_dir}/{sshkey}"
        if not Tools.exists(myhost_sshkey_path):
            Tools.dir_ensure(myhost_sshkey_dir)
            sshkeypath = f"{DIR_HOME}/.ssh/{sshkey}"
            if Tools.exists(sshkeypath):
                shutil.copyfile(sshkeypath, myhost_sshkey_path)

        if self.myenv.config["SSH_KEY_DEFAULT"] != sshkey:
            self.myenv.config["SSH_KEY_DEFAULT"] = sshkey
            self.myenv.config_save()

        return sshkey

    def key_load(self, path=None, name=None, passphrase=None, duration=3600 * 24, die=True):
        """
        load the key on path

        :param path: path for ssh-key, can be left empty then we get the default name which will become path
        :param name: is the name of key which is in ~/.ssh/$name, can be left empty then will be default
        :param passphrase: passphrase for ssh-key, defaults to ""
        :type passphrase: str
        :param duration: duration, defaults to 3600*24
        :type duration: int, optional
        :raises RuntimeError: Path to load sshkey on couldn't be found
        :return: name,path
        """
        if not path and not name:
            raise Tools.exceptions.Input("name or path needs to be specified")
        if name:
            path = Tools.text_replace("{DIR_HOME}/.ssh/%s" % name)
        elif path:
            name = os.path.basename(path)

        if name in self.key_names:
            return

        if not Tools.exists(path):
            if not die:
                return 1
            raise Tools.exceptions.Base("Cannot find path:%s for sshkey (private key)" % path)

        Tools.log("load ssh key: %s" % path)
        os.chmod(path, 0o600)

        if passphrase:
            Tools.log("load with passphrase")
            C = """
                cd /tmp
                echo "exec cat" > ap-cat.sh
                chmod a+x ap-cat.sh
                export DISPLAY=1
                echo {passphrase} | SSH_ASKPASS=./ap-cat.sh ssh-add -t {duration} {path}
                """.format(
                path=path, passphrase=passphrase, duration=duration
            )
            rc, out, err = Tools.execute(C, showout=False, die=False)
            if rc > 0:
                Tools.delete("/tmp/ap-cat.sh")
                if not die:
                    return 2
                raise Tools.exceptions.Operations("Could not load sshkey with passphrase (%s)" % path)
        else:
            # load without passphrase
            cmd = "ssh-add -t %s %s " % (duration, path)
            rc, out, err = Tools.execute(cmd, showout=False, die=False)
            if rc > 0:
                if not die:
                    return 3
                raise Tools.exceptions.Operations("Could not load sshkey without passphrase (%s)" % path)

        self.keys_fix()

        self.reset()

        return name, path

    def keys_fix(self, hdir=None):
        """
        will make sure the pub keys are in the dir
        will also check security
        """
        DIR_HOME = self.myenv.config["DIR_HOME"]
        if not hdir:
            hdir = f"{DIR_HOME}/.ssh"
        for name in self._ssh_keys_names_on_fs(hdir):
            path_pub = f"{hdir}/{name}.pub"
            path_priv = f"{hdir}/{name}"
            if Tools.exists(path_priv) and not Tools.exists(path_pub):
                Tools.execute(f"ssh-keygen -y -f {path_priv} > {path_pub}")
            Tools.execute(f"chmod 644 {path_pub}")
            Tools.execute(f"chmod 600 {path_priv}")

    def key_unload(self, name):
        if name in self._keys:
            path = self.key_path_get(name)
            cmd = "ssh-add -d %s" % (path)
            rc, out, err = Tools.execute(cmd, showout=False, die=True)

    def keys_unload(self):
        cmd = "ssh-add -D"
        rc, out, err = Tools.execute(cmd, showout=False, die=True)

    @property
    def _keys(self):
        """
        """
        if self.__keys is None:
            self._read_keys()
        return self.__keys

    def _read_keys(self):
        return_code, out, err = Tools.execute("ssh-add -L", showout=False, die=False, timeout=2)
        if return_code:
            if return_code == 1 and out.find("The agent has no identities") != -1:
                self.__keys = []
                return []
            else:
                # Remove old socket if can't connect
                if Tools.exists(self.ssh_socket_path):
                    Tools.delete(self.ssh_socket_path)
                    # did not work first time, lets try again
                    return_code, out, err = Tools.execute("ssh-add -L", showout=False, die=False, timeout=10)

        if return_code and self.autostart:
            # ok still issue, lets try to start the ssh-agent if that could be done
            self.start()
            return_code, out, err = Tools.execute("ssh-add -L", showout=False, die=False, timeout=10)
            if return_code == 1 and out.find("The agent has no identities") != -1:
                self.__keys = []
                return []

        if return_code:
            return_code, out, err = Tools.execute("ssh-add", showout=False, die=False, timeout=10)
            if out.find("Error connecting to agent: No such file or directory"):
                raise SSHAgentKeyError("Error connecting to agent: No such file or directory")
            else:
                raise SSHAgentKeyError("Unknown error in ssh-agent, cannot find")

        keys = [line.split() for line in out.splitlines() if len(line.split()) == 3]
        self.__keys = list(map(lambda key: [key[2], " ".join(key[0:2])], keys))
        return self.__keys

    def reset(self):
        self.__keys = None

    @property
    def available(self):
        """
        Check if agent available (does not mean that the sshkey has been loaded, just checks the sshagent is there)
        :return: True if agent is available, False otherwise
        :rtype: bool
        """
        try:
            self._keys
        except SSHAgentKeyError:
            return False
        return True

    def keys_list(self, key_included=False):
        """
        kosmos 'print(j.clients.sshkey.keys_list())'
        list ssh keys from the agent

        :param key_included: defaults to False
        :type key_included: bool, optional
        :raises RuntimeError: Error during listing of keys
        :return: list of paths
        :rtype: list
        """
        if key_included:
            return self._keys
        else:
            return [i[0] for i in self._keys]

    @property
    def key_names(self):

        return [os.path.basename(i[0]) for i in self._keys]

    @property
    def key_paths(self):

        return [i[0] for i in self._keys]

    def key_path_get(self, keyname=None, die=True):
        """
        Returns Path of private key that is loaded in the agent

        :param keyname: name of key loaded to agent to get its path, if empty will check if there is 1 loaded, defaults to ""
        :type keyname: str, optional
        :param die:Raise error if True,else do nothing, defaults to True
        :type die: bool, optional
        :raises RuntimeError: Key not found with given keyname
        :return: path of private key
        :rtype: str
        """
        if not keyname:
            keyname = self.key_default_name
        else:
            keyname = os.path.basename(keyname)
        for item in self.keys_list():
            item2 = os.path.basename(item)
            if item2.lower() == keyname.lower():
                return item
        if die:
            raise Tools.exceptions.Base(
                "Did not find key with name:%s, check its loaded in ssh-agent with ssh-add -l" % keyname
            )

    # def keypub_path_get(self, keyname=None):
    #     path = self.key_path_get(keyname)
    #     return path + ".pub"

    @property
    def keypub(self):
        ks = self.myenv.sshagent._read_keys()
        if len(ks) > 0:
            return ks[0][1]

    def profile_js_configure(self):
        """
        kosmos 'j.clients.sshkey.profile_js_configure()'
        """

        bashprofile_path = os.path.expanduser("~/.profile")
        if not Tools.exists(bashprofile_path):
            Tools.execute("touch %s" % bashprofile_path)

        content = Tools.readFile(bashprofile_path)
        out = ""
        for line in content.split("\n"):
            if line.find("#JSSSHAGENT") != -1:
                continue
            if line.find("SSH_AUTH_SOCK") != -1:
                continue

            out += "%s\n" % line

        out += '[ -z "SSH_AUTH_SOCK" ] && export SSH_AUTH_SOCK=%s' % self.ssh_socket_path
        out = out.replace("\n\n\n", "\n\n")
        out = out.replace("\n\n\n", "\n\n")
        Tools.writeFile(bashprofile_path, out)

    def start(self):
        """

        start ssh-agent, kills other agents if more than one are found

        :raises RuntimeError: Couldn't start ssh-agent
        :raises RuntimeError: ssh-agent was not started while there was no error
        :raises RuntimeError: Could not find pid items in ssh-add -l
        """

        socketpath = self.ssh_socket_path

        Tools.process_kill_by_by_filter("ssh-agent")

        Tools.delete(socketpath)

        if not Tools.exists(socketpath):
            Tools.log("start ssh agent")
            Tools.dir_ensure("{DIR_VAR}")
            rc, out, err = Tools.execute("ssh-agent -a %s" % socketpath, die=False, showout=False, timeout=20)
            if rc > 0:
                raise Tools.exceptions.Base("Could not start ssh-agent, \nstdout:%s\nstderr:%s\n" % (out, err))
            else:
                if not Tools.exists(socketpath):
                    err_msg = "Serious bug, ssh-agent not started while there was no error, " "should never get here"
                    raise Tools.exceptions.Base(err_msg)

                # get pid from out of ssh-agent being started
                piditems = [item for item in out.split("\n") if item.find("pid") != -1]

                # print(piditems)
                if len(piditems) < 1:
                    Tools.log("results was: %s", out)
                    raise Tools.exceptions.Base("Cannot find items in ssh-add -l")

                # pid = int(piditems[-1].split(" ")[-1].strip("; "))
                # socket_path = j.sal.fs.joinPaths("/tmp", "ssh-agent-pid")
                # j.sal.fs.writeFile(socket_path, str(pid))

            return

        self.reset()

    def kill(self):
        """
        Kill all agents if more than one is found

        """
        Tools.process_kill_by_by_filter("ssh-agent")
        Tools.delete(self.ssh_socket_path)
        # Tools.delete("/tmp", "ssh-agent-pid"))
        self.reset()


class ExecutorSSH:
    def __init__(self, addr=None, port=22, debug=False, name="executor"):
        self.name = name
        self.addr = addr
        self.port = port
        self.debug = debug
        self._id = None
        self._env = {}
        self._config = {}
        self.readonly = False
        self.CURDIR = ""
        self._data_path = "/var/executor_data"
        self._init3()

    def reset(self):
        self.state_reset()
        self._init3()
        self.save()

    def _init3(self):
        self._config = None
        # self._env_on_system = None

    @property
    def config(self):
        if not self._config:
            self.load()
        return self._config

    def load(self):
        if self.exists(self._data_path):
            data = self.file_read(self._data_path, binary=True)
            self._config = pickle.loads(data)
        else:
            self._config = {}
        if "DIR_BASE" not in self._config:
            self.systemenv_load()
            self.save()

    def cmd_installed(self, cmd):
        rc, out, err = self.execute("which %s" % cmd, die=False, showout=False)
        if rc > 0:
            return False
        return True

    def save(self):
        """
        only relevant for ssh
        :return:
        """
        data = pickle.dumps(self.config)
        self.file_write(self._data_path, data)

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
        self.myenv.config will also be given to the format function
        content example:
        "{name!s:>10} {val} {n:<10.2f}"  #floating point rounded to 2 decimals
        performance is +100k per sec
        """
        return Tools.text_replace(content=content, args=args, executor=self)

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
        raise Tools.exceptions("not implemented")

    def file_read(self, path, binary=False):
        Tools.log("file read:%s" % path)
        if not binary:
            rc, out, err = self.execute("cat %s" % path, showout=False, interactive=False)
            return out
        else:
            p = Tools._file_path_tmp_get("data")
            self.download(path, dest=p)
            data = Tools.file_read(p)
            Tools.delete(p)
            return data

    def file_write(self, path, content, mode=None, owner=None, group=None, showout=True):
        """
        @param append if append then will add to file
        """
        path = self._replace(path)
        if showout:
            Tools.log("file write:%s" % path)

        assert isinstance(path, str)
        # if isinstance(content, str) and not "'" in content:
        #
        #     cmd = 'echo -n -e "%s" > %s' % (content, path)
        #     self.execute(cmd)
        # else:
        temp = Tools._file_path_tmp_get(ext="data")
        Tools.file_write(temp, content)
        self.upload(temp, path)
        Tools.delete(temp)
        cmd = ""
        if mode:
            cmd += "chmod %s %s && " % (mode, path)
        if owner:
            cmd += "chown %s %s && " % (owner, path)
        if group:
            cmd += "chgrp %s %s &&" % (group, path)
        cmd = cmd.strip().strip("&")
        if cmd:
            self.execute(cmd, showout=False, interactive=False)

        return None

    @property
    def uid(self):
        if not "uid" in self.config:
            self.config["uid"] = str(random.getrandbits(32))
            self.save()
        return self.config["uid"]

    def find(self, path):
        rc, out, err = self.execute("find %s" % path, die=False, interactive=False)
        if rc > 0:
            if err.lower().find("no such file") != -1:
                return []
            raise Tools.exceptions.Base("could not find:%s \n%s" % (path, err))
        res = []
        for line in out.split("\n"):
            if line.strip() == path:
                continue
            if line.strip() == "":
                continue
            res.append(line)
        res.sort()
        return res

    @property
    def container_check(self):
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
        return self.config["IN_DOCKER"]

    @property
    def state(self):
        if "state" not in self.config:
            self.config["state"] = {}
        return self.config["state"]

    def state_exists(self, key):
        key = Tools.text_strip_to_ascii_dense(key)
        return key in self.state

    def state_set(self, key, val=None, save=True):
        key = Tools.text_strip_to_ascii_dense(key)
        if save or key not in self.state or self.state[key] != val:
            self.state[key] = val
            self.save()

    def state_get(self, key, default_val=None):
        key = Tools.text_strip_to_ascii_dense(key)
        if key not in self.state:
            if default_val:
                self.state[key] = default_val
                return default_val
            else:
                return None
        else:
            return self.state[key]

    def state_delete(self, key):
        key = Tools.text_strip_to_ascii_dense(key)
        if key in self.state:
            self.state.pop(key)
            self.save()

    def systemenv_load(self):
        """
        get relevant information from remote system e.g. hostname, env variables, ...
        :return:
        """
        C = """
        set +ex
        if [ -e /sandbox ]; then
            export PBASE=/sandbox
        else
            export PBASE=~/sandbox
        fi
        ls $PBASE  > /dev/null 2>&1 && echo 'ISSANDBOX = 1' || echo 'ISSANDBOX = 0'
        ls "$PBASE/bin/python3"  > /dev/null 2>&1 && echo 'ISSANDBOX_BIN = 1' || echo 'ISSANDBOX_BIN = 0'
        echo UNAME = \""$(uname -mnprs)"\"
        echo "HOME = $HOME"
        echo HOSTNAME = "$(hostname)"
        if [[ "$(uname -s)" == "Darwin" ]]; then
            echo OS_TYPE = "darwin"
        else
            echo OS_TYPE = "ubuntu"
        fi
        echo "CFG_JUMPSCALE = --TEXT--"
        cat $PBASE/cfg/jumpscale_config.msgpack 2>/dev/null || echo ""
        echo --TEXT--
        echo "BASHPROFILE = --TEXT--"
        cat $HOME/.profile_js 2>/dev/null || echo ""
        echo --TEXT--
        echo "ENV = --TEXT--"
        export
        echo --TEXT--
        """
        print(" - load systemenv")
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
            rconfig = Tools.config_load(content=res["CFG_JUMPSCALE"])
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
                self._config[name] = res["CFG_JUMPSCALE"][name]
                return
            if name not in self._config:
                self._config[name] = default

        if self._config == None:
            self._config = {}

        get_cfg("DIR_HOME", res["ENV"]["HOME"])
        get_cfg("DIR_BASE", "/sandbox")
        get_cfg("DIR_CFG", "%s/cfg" % self.config["DIR_BASE"])
        get_cfg("DIR_TEMP", "/tmp")
        get_cfg("DIR_VAR", "%s/var" % self.config["DIR_BASE"])
        get_cfg("DIR_CODE", "%s/code" % self.config["DIR_BASE"])
        get_cfg("DIR_BIN", "/usr/local/bin")

    def execute(
        self,
        cmd,
        die=True,
        showout=False,
        timeout=1000,
        sudo=False,
        replace=True,
        interactive=False,
        retry=None,
        args=None,
        python=False,
        jumpscale=False,
        debug=False,
    ):
        original_command = cmd + ""
        if not args:
            args = {}

        tempfile, cmd = Tools._cmd_process(
            cmd=cmd,
            python=python,
            jumpscale=jumpscale,
            die=die,
            env=args,
            sudo=sudo,
            debug=debug,
            replace=replace,
            executor=self,
        )

        Tools._cmd_check(cmd)

        if interactive:
            cmd2 = "ssh -oStrictHostKeyChecking=no -t root@%s -A -p %s '%s'" % (self.addr, self.port, cmd)
        else:
            cmd2 = "ssh -oStrictHostKeyChecking=no root@%s -A -p %s '%s'" % (self.addr, self.port, cmd)
        r = Tools._execute(
            cmd2,
            interactive=interactive,
            showout=showout,
            timeout=timeout,
            retry=retry,
            die=die,
            original_command=original_command,
        )
        if tempfile:
            Tools.delete(tempfile)
        return r

    def upload(
        self,
        source,
        dest=None,
        recursive=True,
        createdir=False,
        rsyncdelete=True,
        ignoredir=None,
        ignorefiles=None,
        keepsymlinks=True,
        retry=4,
    ):
        """
        :param source:
        :param dest:
        :param recursive:
        :param createdir:
        :param rsyncdelete:
        :param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache__']
        :param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]
        :param keepsymlinks:
        :param showout:
        :return:
        """
        source = self._replace(source)
        if not dest:
            dest = source
        else:
            dest = self._replace(dest)
        if not os.path.exists(source):
            raise Tools.exceptions.Input("path '%s' not found" % source)

        if os.path.isfile(source):
            if createdir:
                destdir = os.path.dirname(source)
                self.dir_ensure(destdir)
            cmd = "scp -P %s %s root@%s:%s" % (self.port, source, self.addr, dest)
            Tools._execute(cmd, showout=True, interactive=False)
            return
        raise Tools.exceptions.RuntimeError("not implemented")
        dest = self._replace(dest)
        if dest[0] != "/":
            raise Tools.exceptions.RuntimeError("need / in beginning of dest path")
        if source[-1] != "/":
            source += "/"
        if dest[-1] != "/":
            dest += "/"
        dest = "%s@%s:%s" % (self.login, self.addr, dest)

    def download(self, source, dest=None, ignoredir=None, ignorefiles=None, recursive=True):
        """
        :param source:
        :param dest:
        :param recursive:
        :param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache__']
        :param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]
        :return:
        """
        if not dest:
            dest = source
        else:
            dest = self._replace(dest)
        source = self._replace(source)

        sourcedir = os.path.dirname(source)
        Tools.dir_ensure(sourcedir)

        destdir = os.path.dirname(dest)
        Tools.dir_ensure(destdir)

        cmd = "scp -P %s root@%s:%s %s" % (self.port, self.addr, source, dest)
        Tools._execute(cmd, showout=True, interactive=False)

    def kosmos(self):
        self.jsxexec("j.shell()")

    def state_reset(self):
        self.config["state"] = {}
        self.save()
