from Jumpscale import j
import os


class SSHClientBase(j.baseclasses.object_config):
    """
    is an ssh client
    """

    _SCHEMATEXT = """
        @url = jumpscale.sshclient.1
        name** = ""
        addr = ""
        port = 22
        #addr_priv = ""
        #port_priv = 22
        login = "root"
        passwd = ""
        sshkey_name = ""
        #if we want to use other key compared to the one we have by default, can specify the name here
        sshkey_deployment = ""  
        proxy = ""
        stdout = True (B)
        forward_agent = True (B)
        allow_agent = True (B)
        client_type = "paramiko,pssh" (E)
        timeout = 60
        config_msgpack = "" (bytes)     
        env_on_system_msgpack = "" (bytes)
        meta = {} (DICT)
        """

    def _init(self, **kwargs):
        self._client_ = None
        self._env_on_system = None
        self._uid = None
        self.executor = j.tools.executor.ssh_get(self)

        self._init3()

    def state_reset(self):
        """
        set the following:

        self.config_msgpack = b""
        self.env_on_system_msgpack = b""

        so it can get reloaded from remote

        :return:
        """
        self.config_msgpack = b""
        self.env_on_system_msgpack = b""

    def reset(self):

        if self._client_:
            # disconnect 2 possible ways on sshclient
            try:
                self._client_.disconnect()
            except:
                pass
            try:
                self._client.close()
            except:
                pass

        self.executor.reset()
        self.save()
        self._init3()

    def _init3(self):

        self.executor._init3()

        self.async_ = False
        # self._private = None
        self._connected = None

        self._transport_ = None

        self._ftp = None
        self._syncer = None

    @property
    def uid(self):
        if self._uid is None:
            if self._id in [0, None, ""]:
                self.save()
            if self._id in [0, None, ""]:
                raise j.exceptions.Base("id cannot be empty")
            self._uid = "%s-%s-%s" % (self.addr, self.port, self._id)
        return self._uid

    def sftp_stat(self, path):
        return self.sftp.stat(path)

    def file_copy(self, local_file, remote_file):
        """Copy local file to host via SFTP/SCP

        Copy is done natively using SFTP/SCP version 2 protocol, no scp command
        is used or required.

        :param local_file: Local filepath to copy to remote host
        :type local_file: str
        :param remote_file: Remote filepath on remote host to copy file to
        :type remote_file: str
        :raises: :py:class:`ValueError` when a directory is supplied to
          ``local_file`` and ``recurse`` is not set
        :raises: :py:class:`IOError` on I/O errors writing files
        :raises: :py:class:`OSError` on OS errors like permission denied
        """
        local_file = self._replace(local_file, paths_executor=False)
        remote_file = self._replace(remote_file)
        if os.path.isdir(local_file):
            raise j.exceptions.Value("Local file cannot be a dir")
        destination = j.sal.fs.getDirName(remote_file)
        self.executor.dir_ensure(destination)
        self._client.scp_send(local_file, remote_file, recurse=False, sftp=None)
        self._log_debug("Copied local file %s to remote destination %s for %s" % (local_file, remote_file, self))

    def _replace(self, txt, paths_executor=True):
        if "{" in txt:
            res = {}
            for key, item in self._data._ddict.items():
                res[key.upper()] = item
            txt = j.core.tools.text_replace(txt, args=res)
        return txt

    # @property
    # def isprivate(self):
    #     if self._private is None:
    #         if self.addr_priv == "":
    #             self._private = False
    #         else:
    #             self._private = j.sal.nettools.tcpPortConnectionTest(self.addr_priv, self.port_priv, 1)
    #     return self._private
    def execute_jumpscale(self, script, **kwargs):
        script = "from Jumpscale import j\n{}".format(script)

        script = j.core.tools.text_replace(script, **kwargs)

        scriptname = j.data.hash.md5_string(script)
        filename = "{}/{}".format(j.dirs.TMPDIR, scriptname)

        j.sal.fs.writeFile(filename, contents=script)
        self.file_copy(filename, filename)  # local -> remote
        self.execute("source /sandbox/env.sh && python3 {}".format(filename))

    @property
    def addr_variable(self):
        return self.addr
        # if self.isprivate:
        #     return self.addr_priv
        # else:
        #     return self.addr

    @property
    def port_variable(self):
        return self.port
        # if self.isprivate:
        #     return self.port_priv
        # else:
        #     return self.port

    @property
    def sshkey_obj(self):
        """
        return right sshkey
        """
        if self.sshkey_name in [None, ""]:
            raise j.exceptions.Base("sshkeyname needs to be specified")
        return j.clients.sshkey.get(name=self.sshkey_name)

    @property
    def isconnected(self):
        if self._connected is None:
            self._connected = j.sal.nettools.tcpPortConnectionTest(self.addr, self.port, 1)
            self.active = True
            self._sshclient = None
            self._ftpclient = None
        return self._connected

    def ssh_authorize(self, pubkeys=None, homedir="/root"):
        """add key to authorized users, if key is specified will get public key from sshkey client,
        or can directly specify the public key. If both are specified key name instance will override public key.

        :param user: user to authorize
        :type user: str
        :param pubkey: public key to authorize, defaults to None
        :type pubkey: str, optional
        """
        if not pubkeys:
            pubkeys = [self.sshkey_obj.pubkey]
        if isinstance(pubkeys, str):
            pubkeys = [pubkeys]
        for sshkey in pubkeys:
            # TODO: need to make sure its only 1 time
            self.execute('echo "{sshkey}" >> {homedir}/.ssh/authorized_keys'.format(**locals()))

    def shell(self, cmd=None):
        if cmd:
            j.shell()
        cmd = "ssh {LOGIN}@{ADDR} -A -p {PORT}"
        cmd = self._replace(cmd)
        j.sal.process.executeWithoutPipe(cmd)

    def mosh(self, ssh_private_key_name=None):
        """
        if private key specified
        :param ssh_private_key:
        :return:
        """
        self.executor.installer.mosh()
        C = j.clients.sshagent._script_get_sshload(keyname=ssh_private_key_name)
        r = self.execute(C)
        cmd = "mosh -ssh='ssh -tt -oStrictHostKeyChecking=no -p {PORT}' {LOGIN}@{ADDR} -p 6000:6100 'bash'"
        cmd = self._replace(cmd)
        j.sal.process.executeWithoutPipe(cmd)

    def kosmos(self, cmd=None):
        j.shell()

    @property
    def syncer(self):
        """
        is a tool to sync local files to your remote ssh instance
        :return:
        """
        if self._syncer is None:
            self._syncer = j.tools.syncer.get(name=self.name, sshclient_names=[self.name])
        return self._syncer

    def portforward_to_local(self, remoteport, localport):
        """
        forward remote port on host to the local one, so we can connect over localhost
        :param remoteport: the port to forward to local
        :param localport: the local tcp port to be used (will terminate on remote)
        :return:
        """
        self.portforwardKill(localport)
        C = "ssh -L %s:localhost:%s %s@%s -p %s" % (remoteport, localport, self.login, self.addr, self.port)
        print(C)
        pm = j.builders.system.processmanager.get()  # need to use other one, no longer working #TODO:
        pm.ensure(cmd=C, name="ssh_%s" % localport, wait=0.5)
        print("Test tcp port to:%s" % localport)
        if not j.sal.nettools.waitConnectionTest("127.0.0.1", localport, 10):
            raise j.exceptions.Base("Cannot open ssh forward:%s_%s_%s" % (self, remoteport, localport))
        print("Connection ok")

    def portforward_kill(self, localport):
        """
        kill the forward
        :param localport:
        :return:
        """
        print("kill portforward %s" % localport)
        pm = j.builders.system.processmanager.get()
        pm.processmanager.stop("ssh_%s" % localport)

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
        if not j.sal.fs.isDir(source):
            if j.sal.fs.isFile(source):
                return self.file_copy(source, dest)
            else:
                raise j.exceptions.Base("only support dir or file for upload")
        dest = self._replace(dest)
        # self._check_base()
        # if dest_prefix != "":
        #     dest = j.sal.fs.joinPaths(dest_prefix, dest)
        if dest[0] != "/":
            raise j.exceptions.RuntimeError("need / in beginning of dest path")
        if source[-1] != "/":
            source += "/"
        if dest[-1] != "/":
            dest += "/"
        dest = "%s@%s:%s" % (self.login, self.addr, dest)
        j.sal.fs.copyDirTree(
            source,
            dest,
            keepsymlinks=keepsymlinks,
            deletefirst=False,
            overwriteFiles=True,
            ignoredir=ignoredir,
            ignorefiles=ignorefiles,
            rsync=True,
            ssh=True,
            sshport=self.port,
            recursive=recursive,
            createdir=createdir,
            rsyncdelete=rsyncdelete,
            showout=True,
            retry=retry,
        )
        self._cache.reset()

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
        source = self._replace(source)
        dest = self._replace(dest)
        if not self.executor.path_isdir(source):
            if self.executor.path_isfile(source):
                return self._client.scp_recv(source, dest, recurse=False, sftp=None, encoding="utf-8")
            else:
                if not self.exists(source):
                    raise j.exceptions.Base("%s does not exists, cannot download" % source)
                raise j.exceptions.Base("src:%s needs to be dir or file" % source)
        # self._check_base()
        # if source_prefix != "":
        #     source = j.sal.fs.joinPaths(source_prefix, source)
        if source[0] != "/":
            raise j.exceptions.RuntimeError("need / in beginning of source path")
        if source[-1] != "/":
            source += "/"
        if dest[-1] != "/":
            dest += "/"

        source = "root@%s:%s" % (self.addr, source)
        j.sal.fs.copyDirTree(
            source,
            dest,
            keepsymlinks=True,
            deletefirst=False,
            overwriteFiles=True,
            ignoredir=ignoredir,
            ignorefiles=ignorefiles,
            rsync=True,
            ssh=True,
            sshport=self.port,
            recursive=recursive,
        )

    def execute(self, cmd, interactive=True, showout=True, replace=True, die=True, timeout=None, script=None):
        """

        :param cmd: cmd to execute, can be multiline or even a script
        :param interactive: run in a way we can interact with the execution
        :param showout: show the stdout?
        :param replace: replace the {} statements in the cmd (script)
        :param die: die if error found
        :param timeout: timeout for execution in seconds
        :param script: if None and its multiline it will be default be executed as script, otherwise do script=False
                        when the len of the cmd is more than 100.000 then will always execute as script
        :return:
        """
        if not isinstance(cmd, str):
            raise j.exceptions.Base("cmd needs to be string")
        if replace:
            cmd = self._replace(cmd)
        if ("\n" in cmd and script in [None, True]) or len(cmd) > 100000:
            return self._execute_script(
                content=cmd,
                die=die,
                showout=showout,
                checkok=None,
                sudo=False,
                interactive=interactive,
                timeout=timeout,
            )
        elif interactive:
            return self._execute_interactive(cmd, showout=showout, die=die)
        else:
            return self._execute(cmd, showout=showout, die=die, timeout=timeout)

    def _execute_interactive(self, cmd, showout=False, replace=True, die=True):
        if "\n" in cmd:
            raise j.exceptions.Base("cannot have \\n in cmd: %s" % cmd)
        if "'" in cmd:
            cmd = cmd.replace("'", '"')
        cmd2 = "ssh -oStrictHostKeyChecking=no -t {LOGIN}@{ADDR} -A -p {PORT} '%s'" % (cmd)
        cmd3 = self._replace(cmd2)
        return j.core.tools.execute(cmd3, interactive=True, showout=False, replace=False, asfile=True, die=die)

    def _execute_script(
        self, content="", die=True, showout=True, checkok=None, sudo=False, interactive=False, timeout=None
    ):
        """
        @param remote can be ip addr or hostname of remote,
                    if given will execute cmds there
        """
        if "sudo -H -SE" in content:
            raise j.exceptions.Base(content)

        if showout:
            self._log_info("EXECUTESCRIPT {}:{}:\n'''\n{}\n'''\n".format(self.addr, self.port, content))

        if content[-1] != "\n":
            content += "\n"

        if die:
            content = "set -e\n{}".format(content)

        dpath = "/tmp/jsxssh_{}.sh".format(j.data.idgenerator.generateRandomInt(1, 100000))

        self.executor.file_write(dpath, content, mode="777")

        # j.sal.fs.writeFile(path, content)
        #
        # # just in case of the same machine.
        # path2 = "/tmp/jsxssh_{}.sh".format(j.data.idgenerator.generateRandomInt(1, 100000))
        # self.file_copy(path, path2)  # is now always on tmp
        # if sudo and "LEDE" not in j.core.platformtype.get(self).osname:
        #     passwd = self.config.data["passwd_"]
        #     cmd = "echo '{}' | sudo -H -SE -p '' bash \"{}\"".format(passwd, path2)
        # else:
        #     cmd = "bash {}".format(path2)

        rc, out, err = self.execute(dpath, die=die, showout=showout, interactive=interactive, timeout=timeout)

        if checkok and die:
            out = self._docheckok(content, out)

        # j.sal.fs.remove(path)
        # self.sftp.unlink(path2)
        return rc, out, err

    def __repr__(self):
        return "SSHCLIENT ssh: %s (%s)" % (self.addr, self.port)

    __str__ = __repr__
