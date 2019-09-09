from Jumpscale import j


class SSHKey(j.baseclasses.object_config):

    _SCHEMATEXT = """
        @url = jumpscale.sshkey.client
        name** = "" (S)
        pubkey = "" (S) 
        allow_agent = True (B)
        passphrase_ = "" (S)
        privkey = "" (S)
        duration = 86400 (I)
        path = "" (S) #path of the private key
        """

    def _init(self, **kwargs):

        self._connected = None

        if self.name == "":
            raise j.exceptions.Base("need to specify name")

        self._autosave = True  # means every write will be saved (is optional to set)

        if self.path == "":
            keyspath = "%s/keys" % (j.sal.fs.getcwd())
            if j.sal.fs.exists(keyspath):
                self.path = keyspath + "/%s" % self.name
                self._save()
            else:
                keyspath_system = j.core.tools.text_replace("{DIR_HOME}/.ssh")
                if j.sal.fs.exists(keyspath_system):
                    self.path = keyspath_system + "/%s" % self.name
                    self._save()

        if not j.sal.fs.exists(self.path):
            if self.privkey:
                j.sal.fs.writeFile(self.path, self.privkey)
            else:
                self.pubkey = ""
                self._save()
                self.generate()
                self._init(**kwargs)
        else:
            if self.privkey:
                c = j.sal.fs.readFile(self.path)
                if not c.strip() == self.privkey.strip():
                    raise j.exceptions.Input("mismatch between key in BCDB and in your filesystem (PRIVKEY)")
            if self.pubkey:
                c = j.sal.fs.readFile("%s.pub" % (self.path))
                if not c.strip() == self.pubkey.strip():
                    raise j.exceptions.Input("mismatch between key in BCDB and in your filesystem (PUBKEY)")

        assert j.sal.fs.exists(self.path)

        if not self.privkey:
            self.privkey = j.sal.fs.readFile(self.path)
            self._save()

        if not self.pubkey and self.privkey:
            path = "%s.pub" % (self.path)
            if not j.sal.fs.exists(path):
                cmd = 'ssh-keygen -f {} -N "{}"'.format(self.path, self.passphrase_)
                j.sal.process.execute(cmd)
            self.pubkey = j.sal.fs.readFile(path)
            self._save()

    def load_from_filesystem(self):
        """
        look for key on filesystem & load in BCDB
        :return:
        """
        self.pubkey = j.sal.fs.readFile("%s.pub" % (self.path))
        self.privkey = j.sal.fs.readFile(self.path)
        self._save()

    def save(self):
        self._init()
        self._save()

    def _save(self):
        j.baseclasses.object_config.save(self)

    def generate(self, reset=False):
        """
        Generate ssh key

        :param reset: if True, then delete old ssh key from dir, defaults to False
        :type reset: bool, optional
        """
        self._log_debug("generate ssh key")

        if reset:
            self.delete_from_sshdir()
            self.pubkey = ""
            self.privkey = ""

        else:
            if not j.sal.fs.exists(self.path):
                if self.privkey != "" and self.pubkey != "":
                    self.write_to_sshdir()

        if self.pubkey:
            raise j.exceptions.Base("cannot generate key because pubkey already known")
        if self.privkey:
            raise j.exceptions.Base("cannot generate key because privkey already known")

        if not j.sal.fs.exists(self.path) or reset:
            cmd = 'ssh-keygen -t rsa -f {} -N "{}"'.format(self.path, self.passphrase_)
            j.sal.process.execute(cmd, timeout=10)
            self._init()

    def delete(self):
        """
        will delete from from config
        """
        self._log_debug("delete:%s" % self.name)
        j.baseclasses.object_config.delete(self)
        # self.delete_from_sshdir()

    def delete_from_sshdir(self):
        j.sal.fs.remove("%s.pub" % self.path)
        j.sal.fs.remove("%s" % self.path)

    def write_to_sshdir(self):
        """
        Write to ssh dir the private and public key
        """
        j.sal.fs.writeFile(self.path, self.privkey)
        j.sal.fs.writeFile(self.path + ".pub", self.pubkey)

    # def sign_ssh_data(self, data):
    #     return self.agent.sign_ssh_data(data)
    #     # TODO: does not work, property needs to be implemented

    def load(self, duration=3600 * 24):
        """
        load ssh key in ssh-agent, if no ssh-agent is found, new ssh-agent will be started

        :param duration: duration, defaults to 3600*24
        :type duration: int, optional
        """
        self._log_debug("load sshkey: %s for duration:%s" % (self.name, duration))
        j.clients.sshagent.key_load(self.path, passphrase=self.passphrase_, duration=duration)

    def unload(self):
        cmd = "ssh-add -d %s " % (self.path)
        rc = 0
        while rc == 0:
            rc, out, err = j.sal.process.execute(cmd, die=False)  # there could be more than 1 instance
        j.core.myenv.sshagent.__keys = None
        if err.find("agent refused operation") != -1:
            raise j.exceptions.Base("agent did not allow operation")
        j.shell()
        assert self.is_loaded() == False

    def is_loaded(self):
        """
        check if key is loaded in the ssh agent

        :return: whether ssh key was loadeed in ssh agent or not
        :rtype: bool
        """
        for id, key in j.core.myenv.sshagent._read_keys():
            if " " in key.strip():
                keypub = key.split(" ")[1].strip()
            else:
                keypub = key.strip()
            if keypub == keypub:
                return True
        self._log_debug("ssh key: %s is not loaded", self.name)
        return False

    @property
    def pubkey_only(self):
        """
        return the key only with no type e.g.ssh-rsa or email/username
        :return:
        """
        if not self.pubkey:
            raise j.exceptions.Base("pubkey is None")
        r = self.pubkey.split(" ")
        if len(r) == 2:
            return r[1]
        elif len(r) == 3:
            return r[1]
        else:
            raise j.exceptions.Base("format of pubkey not ok:%s" % self.pubkey)
