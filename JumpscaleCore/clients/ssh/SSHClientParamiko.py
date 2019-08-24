import io
from io import StringIO
import paramiko
import functools
import threading
import queue
import socket
import time
import os
from Jumpscale import j
from paramiko.ssh_exception import AuthenticationException, BadHostKeyException, SSHException, BadAuthenticationType
from .SSHClientBase import SSHClientBase
from .StreamReader import StreamReader


class SSHClientParamiko(SSHClientBase):
    """
    is an ssh client
    """

    def _init(self, **kwargs):
        SSHClientBase._init(self, **kwargs)

        if self.passwd:
            self._forward_agent = False
            self._look_for_keys = False
            # self.key_filename = None
            self.passphrase = None
        else:
            self._look_for_keys = True

    def _test_local_agent(self):
        """
        try to connect to the local ssh-agent
        return True if local agent is running, False if not
        """
        agent = paramiko.Agent()
        if len(agent.get_keys()) == 0:
            return False
        else:
            return True

    @property
    def _client(self):
        if self._client_ is None:
            self._connect()
        return self._client_

    @property
    def sftp(self):
        if self._ftp is None:
            # self._ftp = self._client.open_sftp()
            """Make SFTP client from open transport"""
            transport = self._transport
            transport.open_session()
            self._ftp = paramiko.SFTPClient.from_transport(transport)

        return self._ftp

    def _parent_paths_split(self, file_path, sep=None):
        sep = os.path.sep if sep is None else sep
        try:
            destination = sep.join([_dir for _dir in file_path.split(os.path.sep) if _dir][:-1])
        except IndexError:
            destination = ""
        if file_path.startswith(sep) or not destination:
            destination = sep + destination
        return destination

    # def _copy_dir(self, local_dir, remote_dir, sftp):
    #     """Call file_copy on every file in the specified directory, copying
    #     them to the specified remote directory."""
    #     file_list = os.listdir(local_dir)
    #     for file_name in file_list:
    #         local_path = os.path.join(local_dir, file_name)
    #         remote_path = '/'.join([remote_dir, file_name])
    #         self.file_copy(local_path, remote_path, recurse=True,
    #                        sftp=sftp)

    @property
    def _transport(self):
        if self._transport_ is None:
            if self._client is None:
                raise j.exceptions.RuntimeError("Could not connect to %s:%s" % (self.addr, self.port))
            self._transport_ = self._client.get_transport()
            if self._transport_ is None:
                raise j.exceptions.Base("transport cannot be None")
        return self._transport_

    def _connect(self):
        if self.addr == "" or self.port == 0:
            raise j.exceptions.Base("addr or port cannot be empty.")

        self._log_debug("Test sync ssh connection to %s:%s:%s" % (self.addr, self.port, self.login))

        if j.sal.nettools.waitConnectionTest(self.addr, self.port, self.timeout) is False:
            self._log_error(
                "Cannot connect to ssh server %s:%s with login:%s and using sshkey:%s"
                % (self.addr, self.port, self.login, self.sshkey_name)
            )
            raise j.exceptions.Base("Could not connect to addr:'%s' port:'%s'" % (self.addr, self.port))

        # self.pkey = None
        # if self.key_filename is not None and self.key_filename != '':
        #     self.pkey = paramiko.RSAKey.from_private_key_file(
        #         self.sshkey.path, password=self.sshkey.passphrase_)

        self._client_ = paramiko.SSHClient()
        self._client_.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # if self.key_filename:
        #     self.allow_agent = True
        #     self._look_for_keys = True
        #     # if j.clients.ssh.SSHKeyGetPathFromAgent(self.key_filename, die=False) is not None and not self.passphrase_:
        #     #     j.clients.ssh.ssh_keys_load(self.key_filename)

        start = j.data.time.getTimeEpoch()

        while start + self.timeout > j.data.time.getTimeEpoch():
            try:
                self._log_info("connect to:%s" % self.addr)
                self._log_debug("connect with port :%s" % self.port)
                self._log_debug("connect with username :%s" % self.login)
                self._log_debug("connect with password :%s" % self.passwd)
                # self._log_debug("connect with pkey :%s" % self.pkey)
                self._log_debug("connect with allow_agent :%s" % self.allow_agent)
                self._log_debug("connect with look_for_keys :%s" % self._look_for_keys)
                self._log_debug("Timeout is : %s " % self.timeout)
                self._client_.connect(
                    self.addr,
                    int(self.port),
                    username=self.login,
                    password=self.passwd,
                    # pkey=self.pkey,
                    allow_agent=self.allow_agent,
                    look_for_keys=self._look_for_keys,
                    timeout=2.0,
                    banner_timeout=3.0,
                )
                self._log_info("connection ok")
                return self._client_
            except BadAuthenticationType as e:
                raise e
            except (BadHostKeyException, AuthenticationException) as e:
                self._log_error("Authentification error. Aborting connection : %s" % str(e))
                self._log_error(str(e))
                raise j.exceptions.RuntimeError(str(e))

            except (SSHException, socket.error) as e:
                self._log_error("Unexpected error in socket connection for ssh. Aborting connection and try again.")
                self._log_error(e)
                self._client_.close()
                # self.reset()
                time.sleep(0.1)
                continue

            except Exception as e:
                # j.clients.ssh.removeFromCache(self)
                msg = "Could not connect to ssh on %s@%s:%s. Error was: %s" % (self.login, self.addr, self.port, e)
                raise j.exceptions.RuntimeError(msg)

        raise j.exceptions.RuntimeError("Impossible to create SSH connection to %s:%s" % (self.addr, self.port))

    def _execute(self, cmd, showout=True, die=True, timeout=None):
        """
        run cmd & return
        return: (retcode,out_err)
        """
        ch = None

        ch = self._transport.open_session()

        # if self._forward_agent:
        #     paramiko.agent.AgentRequestHandler(ch)

        # execute the command on the remote server
        ch.exec_command(cmd)
        # indicate that we're not going to write to that channel anymore
        ch.shutdown_write()
        # create file like object for stdout and stderr to read output of
        # command
        stdout = ch.makefile("r")
        stderr = ch.makefile_stderr("r")

        # Start stream reader thread that will read strout and strerr
        inp = queue.Queue()
        outReader = StreamReader(stdout, ch, inp, "O")
        errReader = StreamReader(stderr, ch, inp, "E")
        outReader.start()
        errReader.start()

        err = io.StringIO()  # error buffer
        out = io.StringIO()  # stdout buffer
        out_eof = False
        err_eof = False

        while out_eof is False or err_eof is False:
            try:
                chan, line = inp.get(block=True, timeout=1.0)
                if chan == "T":
                    if line == "O":
                        out_eof = True
                    elif line == "E":
                        err_eof = True
                    continue
                line = j.core.text.toAscii(line)
                if chan == "O":
                    if showout:
                        self._log_debug(line.rstrip())
                    out.write(line)
                elif chan == "E":
                    if showout:
                        self._log_error(line.rstrip())
                    err.write(line)
            except queue.Empty:
                pass

        # stop the StreamReader and wait for the thread to finish
        outReader._stopped = True
        errReader._stopped = True
        outReader.join()
        errReader.join()

        # indicate that we're not going to read from this channel anymore
        ch.shutdown_read()
        # close the channel
        ch.close()

        # close all the pseudofiles
        stdout.close()
        stderr.close()

        rc = ch.recv_exit_status()

        if rc and die:
            raise j.exceptions.RuntimeError(
                "Cannot execute (ssh):\n%s\noutput:\n%serrors:\n%s" % (cmd, out.getvalue(), err.getvalue())
            )

        return rc, out.getvalue(), err.getvalue()

    # def SSHAuthorizeKey(
    #         self,
    #         keyname=None, keydata=None):
    #     """
    #     @keyname name of the key as loaded in ssh-agent if set keydata will be ignored(this requires ssh-agent to be loaded)
    #     @keydata actual data of private key if set keyname will be ignored
    #     """
    #     if keydata:
    #         key_des = StringIO(keydata)
    #         p = paramiko.RSAKey.from_private_key(key_des)
    #         key = '%s ' % p.get_name() + p.get_base64()
    #     elif not keyname:
    #         raise j.exceptions.Input("keyname and keydata can't be both empty")
    #     else:
    #         key = j.clients.ssh.SSHKeyGetFromAgentPub(keyname)

    #     rc, _, _ = self.execute(
    #         "echo '%s' | sudo -S bash -c 'test -e /root/.ssh'" % self.passwd, die=False)
    #     mkdir_cmd = ''
    #     if rc > 0:
    #         mkdir_cmd = 'mkdir -p /root/.ssh;'

    #     cmd = '''echo '%s' | sudo -S bash -c "%s echo '\n%s' >> /root/.ssh/authorized_keys; chmod 644 /root/.ssh/authorized_keys;chown root:root /root/.ssh/authorized_keys"''' % (
    #         self.passwd, mkdir_cmd, key)
    #     self.execute(cmd, showout=False)

    #     j.clients.ssh.remove_item_from_known_hosts(self.addr)
