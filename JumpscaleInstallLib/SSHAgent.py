import os
import shutil
import sys


class SSHAgentKeyError(Exception):
    pass


class SSHAgent:
    _myenv = None

    def __init__(self, myenv):
        self._my = myenv
        self._tools = myenv.tools
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

        socketpath = self._tools.text_replace("{DIR_VAR}/sshagent_socket")
        os.environ["SSH_AUTH_SOCK"] = socketpath
        return socketpath

    def _key_name_get(self, name=None):

        if not name:
            if self._my.config["SSH_KEY_DEFAULT"]:
                name = self._my.config["SSH_KEY_DEFAULT"]
            elif self._my.interactive:
                name = self._tools.ask_string("give name for your sshkey,default='default'")
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
        self._tools.log("generate ssh key")
        name = self._key_name_get(name)

        if not passphrase:
            if self._my.interactive:
                passphrase = self._tools.ask_password("passphrase for ssh key to generate (empty=None)", emptyok=True)

        path = self._tools.text_replace("{DIR_HOME}/.ssh/%s" % name)
        self._tools.dir_ensure("{DIR_HOME}/.ssh")

        if reset:
            self._tools.delete("%s" % path)
            self._tools.delete("%s.pub" % path)

        if not self._tools.exists(path) or reset:
            if passphrase:
                cmd = f'ssh-keygen -t rsa -f {path} -N "{passphrase}" -C {name}'
            else:
                cmd = f"ssh-keygen -t rsa -f {path} -C {name}"
            self._tools.execute(cmd, timeout=10)

            self._tools.log("load generated sshkey: %s" % path)

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
        DIR_HOME = self._my.config["DIR_HOME"]
        if not hdir:
            hdir = f"{DIR_HOME}/.ssh"
        choices = []
        if self._tools.exists(hdir):
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

        DIR_HOME = self._my.config["DIR_HOME"]
        DIR_BASE = self._my.config["DIR_BASE"]

        def ask_key(key_names):
            if len(key_names) == 1:
                name = key_names[0]
            elif len(key_names) == 0:
                return None
            else:
                name = self._tools.ask_choices("Which is your default sshkey to use", key_names)
            return name

        self._keys  # will fetch the keys if not possible will show error

        if "SSH_KEY_DEFAULT" in self._my.config and self._my.config["SSH_KEY_DEFAULT"]:
            sshkey = self._my.config["SSH_KEY_DEFAULT"]
            if not sshkey in self.key_names:
                res = self.key_load(name=sshkey, die=False)
                if res == None:
                    return None
                sshkey = None
                self._my.config["SSH_KEY_DEFAULT"] = ""
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
        if not sshkey and self._tools.exists(myhost_sshkey_dir):
            # lets check if there is a key in the myhost dir
            res = os.listdir(myhost_sshkey_dir)
            if len(res) == 1:
                sshkey = res[0]
                myhost_sshkey_path = f"{myhost_sshkey_dir}/{sshkey}"
                sshkeypath = f"{DIR_HOME}/.ssh/{sshkey}"
                shutil.copyfile(myhost_sshkey_path, sshkeypath)

        # if no key yet, need to generate
        if not sshkey:
            if self._tools.ask_yes_no("ok to generate a default ssh key?"):
                sshkey = self._key_name_get()
                sshkeypath = self.key_generate(name=sshkey)
            else:
                print("CANNOT CONTINUE, PLEASE GENERATE AN SSHKEY AND RESTART")
                sys.exit(1)

        if not sshkey in self.key_names:
            if self.DockerFactory.indocker():
                raise self._tools.exceptions.Base("sshkey should be passed forward by means of SSHAgent")
            self.key_load(name=sshkey)

        if not sshkey in self.key_names:
            raise self._tools.exceptions.Input(f"SSH key '{sshkey}' was not loaded, should have been by now.")

        myhost_sshkey_path = f"{myhost_sshkey_dir}/{sshkey}"
        if not self._tools.exists(myhost_sshkey_path):
            self._tools.dir_ensure(myhost_sshkey_dir)
            sshkeypath = f"{DIR_HOME}/.ssh/{sshkey}"
            if self._tools.exists(sshkeypath):
                shutil.copyfile(sshkeypath, myhost_sshkey_path)

        if self._my.config["SSH_KEY_DEFAULT"] != sshkey:
            self._my.config["SSH_KEY_DEFAULT"] = sshkey
            self._my.config_save()

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
            raise self._tools.exceptions.Input("name or path needs to be specified")
        if name:
            path = self._tools.text_replace("{DIR_HOME}/.ssh/%s" % name)
        elif path:
            name = os.path.basename(path)

        if name in self.key_names:
            return

        if not self._tools.exists(path):
            if not die:
                return 1
            raise self._tools.exceptions.Base("Cannot find path:%s for sshkey (private key)" % path)

        self._tools.log("load ssh key: %s" % path)
        os.chmod(path, 0o600)

        if passphrase:
            self._tools.log("load with passphrase")
            C = """
                cd /tmp
                echo "exec cat" > ap-cat.sh
                chmod a+x ap-cat.sh
                export DISPLAY=1
                echo {passphrase} | SSH_ASKPASS=./ap-cat.sh ssh-add -t {duration} {path}
                """.format(
                path=path, passphrase=passphrase, duration=duration
            )
            rc, out, err = self._tools.execute(C, showout=False, die=False)
            if rc > 0:
                self._tools.delete("/tmp/ap-cat.sh")
                if not die:
                    return 2
                raise self._tools.exceptions.Operations("Could not load sshkey with passphrase (%s)" % path)
        else:
            # load without passphrase
            cmd = "ssh-add -t %s %s " % (duration, path)
            rc, out, err = self._tools.execute(cmd, showout=False, die=False)
            if rc > 0:
                if not die:
                    return 3
                raise self._tools.exceptions.Operations("Could not load sshkey without passphrase (%s)" % path)

        self.keys_fix()

        self.reset()

        return name, path

    def keys_fix(self, hdir=None):
        """
        will make sure the pub keys are in the dir
        will also check security
        """
        DIR_HOME = self._my.config["DIR_HOME"]
        if not hdir:
            hdir = f"{DIR_HOME}/.ssh"
        for name in self._ssh_keys_names_on_fs(hdir):
            path_pub = f"{hdir}/{name}.pub"
            path_priv = f"{hdir}/{name}"
            if self._tools.exists(path_priv) and not self._tools.exists(path_pub):
                self._tools.execute(f"ssh-keygen -y -f {path_priv} > {path_pub}")
            self._tools.execute(f"chmod 644 {path_pub}")
            self._tools.execute(f"chmod 600 {path_priv}")

    def key_unload(self, name):
        if name in self._keys:
            path = self.key_path_get(name)
            cmd = "ssh-add -d %s" % (path)
            rc, out, err = self._tools.execute(cmd, showout=False, die=True)

    def keys_unload(self):
        cmd = "ssh-add -D"
        rc, out, err = self._tools.execute(cmd, showout=False, die=True)

    @property
    def _keys(self):
        """
        """
        if self.__keys is None:
            self._read_keys()
        return self.__keys

    def _read_keys(self):
        return_code, out, err = self._tools.execute("ssh-add -L", showout=False, die=False, timeout=2)
        if return_code:
            if return_code == 1 and out.find("The agent has no identities") != -1:
                self.__keys = []
                return []
            else:
                # Remove old socket if can't connect
                if self._tools.exists(self.ssh_socket_path):
                    self._tools.delete(self.ssh_socket_path)
                    # did not work first time, lets try again
                    return_code, out, err = self._tools.execute("ssh-add -L", showout=False, die=False, timeout=10)

        if return_code and self.autostart:
            # ok still issue, lets try to start the ssh-agent if that could be done
            self.start()
            return_code, out, err = self._tools.execute("ssh-add -L", showout=False, die=False, timeout=10)
            if return_code == 1 and out.find("The agent has no identities") != -1:
                self.__keys = []
                return []

        if return_code:
            return_code, out, err = self._tools.execute("ssh-add", showout=False, die=False, timeout=10)
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
            raise self._tools.exceptions.Base(
                "Did not find key with name:%s, check its loaded in ssh-agent with ssh-add -l" % keyname
            )

    # def keypub_path_get(self, keyname=None):
    #     path = self.key_path_get(keyname)
    #     return path + ".pub"

    @property
    def keypub(self):
        ks = self._my.sshagent._read_keys()
        if len(ks) > 0:
            return ks[0][1]

    def profile_js_configure(self):
        """
        kosmos 'j.clients.sshkey.profile_js_configure()'
        """

        bashprofile_path = os.path.expanduser("~/.profile")
        if not self._tools.exists(bashprofile_path):
            self._tools.execute("touch %s" % bashprofile_path)

        content = self._tools.readFile(bashprofile_path)
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
        self._tools.writeFile(bashprofile_path, out)

    def start(self):
        """

        start ssh-agent, kills other agents if more than one are found

        :raises RuntimeError: Couldn't start ssh-agent
        :raises RuntimeError: ssh-agent was not started while there was no error
        :raises RuntimeError: Could not find pid items in ssh-add -l
        """

        socketpath = self.ssh_socket_path

        self._tools.process_kill_by_by_filter("ssh-agent")

        self._tools.delete(socketpath)

        if not self._tools.exists(socketpath):
            self._tools.log("start ssh agent")
            self._tools.dir_ensure("{DIR_VAR}")
            rc, out, err = self._tools.execute("ssh-agent -a %s" % socketpath, die=False, showout=False, timeout=20)
            if rc > 0:
                raise self._tools.exceptions.Base("Could not start ssh-agent, \nstdout:%s\nstderr:%s\n" % (out, err))
            else:
                if not self._tools.exists(socketpath):
                    err_msg = "Serious bug, ssh-agent not started while there was no error, " "should never get here"
                    raise self._tools.exceptions.Base(err_msg)

                # get pid from out of ssh-agent being started
                piditems = [item for item in out.split("\n") if item.find("pid") != -1]

                # print(piditems)
                if len(piditems) < 1:
                    self._tools.log("results was: %s", out)
                    raise self._tools.exceptions.Base("Cannot find items in ssh-add -l")

                # pid = int(piditems[-1].split(" ")[-1].strip("; "))
                # socket_path = j.sal.fs.joinPaths("/tmp", "ssh-agent-pid")
                # j.sal.fs.writeFile(socket_path, str(pid))

            return

        self.reset()

    def kill(self):
        """
        Kill all agents if more than one is found

        """
        self._tools.process_kill_by_by_filter("ssh-agent")
        self._tools.delete(self.ssh_socket_path)
        # self._tools.delete("/tmp", "ssh-agent-pid"))
        self.reset()
