import io
import os
from Jumpscale import j
from .SSHClientBase import SSHClientBase
import time
import gevent

# import ssh2.sftp
# from ssh2.session import Session


class SSHClient(SSHClientBase):
    def _init2(self, **kwargs):

        self._logger_prefix = "ssh client: %s:%s(%s)" % (self.addr, self.port, self.login)
        self._logger_enable()

        self.__ssh2 = None

        if self.passwd == "" and self.sshkey_name == "":
            if j.clients.sshagent.key_default_name:
                self.sshkey_name = j.clients.sshagent.key_default_name
                self.save()

    # def _ssh2(self):
    #     if not self.__ssh2:
    #         self.__ssh2.Session()
    #         self.__ssh2.direct_tcpip(self.add, self.port)
    #     return self.__ssh2

    @property
    def _client(self):
        if self._client_ is None:

            passwd = self.passwd

            if self.sshkey_name:
                pkey = self.sshkey_obj.path if (self.sshkey_obj and self.sshkey_obj.path) else None
                if pkey:
                    passwd = self.sshkey_obj.passphrase_

            if self.allow_agent:
                passwd = None
                pkey = None

            passwd = None

            from pssh.clients import SSHClient

            self._log_debug(
                "ssh connection: %s@%s:%s (passwd:%s,key:%s)" % (self.login, self.addr, self.port, passwd, pkey)
            )

            try:
                self._client_ = SSHClient(
                    host=self.addr,
                    user=self.login,
                    password=passwd,
                    port=self.port,
                    # proxy_pkey=pkey,
                    num_retries=10,
                    allow_agent=self.allow_agent,
                    timeout=self.timeout,
                    retry_delay=1,
                )
            except Exception as e:
                if str(e).find("Error connecting to host") != -1:
                    msg = e.args[0] % e.args[1:]
                    raise j.exceptions.Base("PSSH:%s" % msg)
                raise

        return self._client_

    def _execute(self, cmd, showout=True, die=True, timeout=None):

        # print ("execute", cmd, showout, die, timeout)
        # channel, _, stdout, stderr, _ = self._client.run_command(cmd, timeout=timeout, use_pty=True)

        output = self._client.run_command(cmd)
        channel, addr, stdout, stderr, _ = output
        # client = output[0]
        # channel = client.channel
        # stdout = client.stdout
        # stderr = client.stderr

        # for host, host_output in output.items():
        #     for line in host_output.stdout:
        #         print(line)

        def _consume_stream(stream, printer, buf=None):
            buffer = buf or io.StringIO()
            for line in stream:
                buffer.write(line + "\n")
                if showout:
                    printer(line)
            return buffer

        out = _consume_stream(stdout, self._log_debug)
        err = _consume_stream(stderr, self._log_error)
        # self._client.wait_finished(channel)
        _consume_stream(stdout, self._log_debug, out)
        _consume_stream(stderr, self._log_error, err)

        rc = channel.get_exit_status()
        output = out.getvalue()
        out.close()
        error = err.getvalue()
        err.close()
        channel.close()

        if rc and die:
            raise j.exceptions.RuntimeError("Cannot execute (ssh):\n%s\noutput:\n%serrors:\n%s" % (cmd, output, error))

        return rc, output, error

    def file_write(self, path, content, mode=None, owner=None, group=None):
        temp = j.sal.fs.getTmpFilePath()
        j.sal.fs.writeFile(filename=temp, contents=content, append=False)
        self.file_copy(temp, path)
        j.sal.fs.remove(temp)
        cmd = ""
        if mode:
            # 0o755
            cmd += "chmod %s %s && " % (mode, path)
        if owner:
            cmd += "chown %s %s && " % (owner, path)
        if group:
            cmd += "chgrp %s %s &&" % (group, path)
        cmd = cmd.strip().strip("&")
        if cmd:
            self.execute(cmd, showout=False, interactive=False)

        # flags = ssh2.sftp.LIBSSH2_FXF_CREAT
        # if append:
        #     flags |= ssh2.sftp.LIBSSH2_FXF_APPEND
        # else:
        #     flags |= ssh2.sftp.LIBSSH2_FXF_WRITE
        # file = self.sftp.open(path, flags, mode)
        # file.write(content)
        # file.close()

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
        if os.path.isdir(local_file):
            raise j.exceptions.Value("Local file cannot be a dir")
        destination = j.sal.fs.getDirName(remote_file)
        try:
            res = self._client.scp_send(local_file, remote_file, recurse=False)
        except Exception as e:
            self.execute("mkdir -p %s" % destination)
            res = self._client.scp_send(local_file, remote_file, recurse=False)

        if res:
            gevent.joinall(res)
        self._log_info("Copied local file %s to remote destination %s for %s" % (local_file, remote_file, self))

    def sftp_stat(self, path):
        res = self.sftp.stat(path)
        counter = 0
        while isinstance(res, int):
            res = self.sftp.stat(path)
            counter += 1
            time.sleep(0.1)
            if counter > 10:
                raise j.exceptions.Base("sft gives back int:%s for %s" % (res, path))
        return res

    # def connectViaProxy(self, host, username, port, identityfile, proxycommand=None):
    #     # TODO: Fix this
    #     self.usesproxy = True
    #     client = paramiko.SSHClient()
    #     client._policy = paramiko.WarningPolicy()
    #     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #     import os.path
    #     self.host = host
    #     cfg = {'hostname': host, 'username': username, "port": port}
    #     self.addr = host
    #     self.user = username

    #     if identityfile is not None:
    #         cfg['key_filename'] = identityfile
    #         self.key_filename = cfg['key_filename']

    #     if proxycommand is not None:
    #         cfg['sock'] = paramiko.ProxyCommand(proxycommand)
    #     cfg['timeout'] = 5
    #     cfg['allow_agent'] = True
    #     cfg['banner_timeout'] = 5
    #     self.cfg = cfg
    #     self._forward_agent = True
    #     self._client = client
    #     self._client.connect(**cfg)

    #     return self._client

    @property
    def sftp(self):

        if self._ftp is None:
            self._ftp = self._client._make_sftp()
        return self._ftp

    def _close(self):
        # TODO: make sure we don't need to clean anything
        pass
