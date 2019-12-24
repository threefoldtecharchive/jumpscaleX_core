from Jumpscale import j
import os
import gevent

import time


class SSHClientBase(j.baseclasses.object_config):
    """
    is an ssh client
    """

    _SCHEMATEXT = """
        @url = jumpscale.sshclient.1
        name** = ""
        addr = ""
        port = 22
        login = "root"
        passwd = ""
        sshkey_name = ""
        proxy = ""
        stdout = True (B)
        forward_agent = True (B)
        allow_agent = True (B)
        # client_type = "paramiko,pssh" (E)
        timeout = 60
        """

    def _init(self, **kwargs):
        self._client_ = None
        self._executor = None
        self._wireguard = None
        self._init3()
        if self.sshkey_name and self.sshkey_name not in j.core.myenv.sshagent.key_names:
            j.core.myenv.sshagent.start()
            self.sshkey_obj.load()

    @property
    def executor(self):
        if not self._executor:
            self._executor = j.tools.executor.ssh_get(self)
        return self._executor

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

        self._init3()

    def _init3(self):
        self.async_ = False
        self._connected = None
        self._transport_ = None
        self._ftp = None
        self._syncer = None

    @property
    def uid(self):
        return "%s-%s-%s" % (self.addr, self.port, self.name)

    def sftp_stat(self, path):
        path = self.executor._replace(path)
        return self.sftp.stat(path)

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

    def ssh_authorize(self, pubkeys=None, homedir="/root", interactive=True):
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
            self.execute(
                'echo "{sshkey}" >> {homedir}/.ssh/authorized_keys'.format(**locals()), interactive=interactive
            )

    def mosh(self, cmd=None, ssh_private_key_name=None, interactive=True):
        """
        if private key specified
        :param ssh_private_key:
        :return:
        """
        self.executor.installer.mosh()
        C = j.clients.sshagent._script_get_sshload(keyname=ssh_private_key_name)
        r = self.execute(C, interactive=interactive)
        cmd = "mosh -ssh='ssh -tt -oStrictHostKeyChecking=no -p {PORT}' {LOGIN}@{ADDR} -p 6000:6100 'bash'"
        cmd = self.executor._replace(cmd, args={"LOGIN": self.login, "ADDR": self.addr, "PORT": self.port})
        j.sal.process.executeWithoutPipe(cmd)

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
        forward remote port on ssh host to the local one, so we can connect over localhost to the remote one
        :param remoteport: the port to forward to local
        :param localport: the local tcp port to be used (will terminate on remote)
        :return:
        """
        self.portforward_kill(localport)
        C = f"ssh -4 -f -N -L {localport}:127.0.0.1:{remoteport} {self.login}@{self.addr} -p {self.port}"
        print(C)

        j.sal.process.execute(C)
        print("Test tcp port to:%s" % localport)
        if not j.sal.nettools.waitConnectionTest("localhost", localport, 10):
            raise j.exceptions.Base("Cannot open ssh forward:%s_%s_%s" % (self, remoteport, localport))
        print("Connection ok")

    def portforward_to_remote(self, remoteport, localport, timeout=50):
        """
        forward local port to remote host port
        :param remoteport: port used on ssh host
        :param localport: the local tcp port to be used
        :return:
        """
        if not j.sal.nettools.tcpPortConnectionTest("localhost", localport):
            raise j.exceptions.Base(
                "Cannot open ssh forward:%s_%s_%s (local port:%s)" % (self, remoteport, localport, localport)
            )
        # self.portforwardKill(localport)
        C = f"ssh -4 -R {remoteport}:127.0.0.1:{localport} {self.login}@{self.addr} -p {self.port}"
        print(C)
        key = f"{self.addr}_{self.port}_{remoteport}_{localport}"
        cmd = j.servers.startupcmd.get(name=key)
        cmd.cmd_start = C
        cmd.ports = []
        cmd.timeout = 20
        cmd.process_strings = []  # ["ssh -R 8112:localhost:8111 root@explorer.testnet.grid.tf -p 22"]
        cmd.executor = "tmux"
        cmd.start()

        start = j.data.time.epoch
        end = start + timeout
        while j.data.time.epoch < end:
            if self.tcp_remote_port_check("127.0.0.1", remoteport):
                self._log_info(f"Connection ok for {remoteport} to local:{localport}")
                return
            time.sleep(0.1)
            # if not cmd.is_running():
            #     raise j.exceptions.Base("could not start:%s in tmux" % C)
        raise j.exceptions.Base("could not start:%s in tmux" % C)

    def tcp_remote_port_check(self, addr="localhost", port=22):
        cmd = f"nc -zv {addr} {port}"
        rc, _, _ = self.execute(cmd)
        if rc == 0:
            return True
        else:
            return False

    def portforward_kill(self, localport):
        """
        kill the forward
        :param localport:
        :return:
        """
        print("kill portforward %s" % localport)
        j.sal.process.killProcessByPort(localport)

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
        source = j.core.tools.text_replace(source)  # this needs to be the local one
        if not dest:
            dest = source
        if not j.sal.fs.isDir(source):
            if j.sal.fs.isFile(source):
                return self.file_copy(source, dest)
            else:
                raise j.exceptions.Base("only support dir or file for upload")
        dest = self.executor._replace(dest)
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
        source = self.executor._replace(source)
        dest = j.core.tools.text_replace(dest)  # this is on the local system so need to use the local replace
        if not self.executor.path_isdir(source):
            if self.executor.path_isfile(source):
                res = self._client.scp_recv(source, dest, recurse=False)
                gevent.joinall(res)
                self._log_info("Copied remote file %s to loacl destination %s for %s" % (dest, source, self))
            else:
                if not self.exists(source):
                    raise j.exceptions.Base("%s does not exists, cannot download" % source)
                raise j.exceptions.Base("src:%s needs to be dir or file" % source)
        # self._check_base()
        # if source_prefix != "":
        #     source = j.sal.fs.joinPaths(source_prefix, source)
        if source[0] != "/":
            raise j.exceptions.RuntimeError("need / in beginning of source path")
        if source[-1] != "/" and not self.executor.path_isfile(source):
            source += "/"
        if dest[-1] != "/" and not self.executor.path_isfile(dest):
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
            cmd = self.executor._replace(cmd)
        if ("\n" in cmd and script in [None, True]) or len(cmd) > 100000:
            raise RuntimeError("NOT IMPLEMENTED")
            # is it still needed ?
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
        cmd3 = self.executor._replace(cmd2, args={"LOGIN": self.login, "ADDR": self.addr, "PORT": self.port})
        return j.core.tools.execute(cmd3, interactive=True, showout=False, replace=False, asfile=True, die=die)

    def __repr__(self):
        return "SSHCLIENT ssh: %s (%s)" % (self.addr, self.port)

    __str__ = __repr__
