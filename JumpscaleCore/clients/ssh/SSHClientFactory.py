from Jumpscale import j
from .SSHClient import SSHClient
from .SSHClientParamiko import SSHClientParamiko
from .SSHClientBase import SSHClientBase


class SSHClientFactory(j.baseclasses.object_config_collection_testtools):

    __jslocation__ = "j.clients.ssh"
    _CHILDCLASS = SSHClientBase
    _SCHEMATEXT = _CHILDCLASS._SCHEMATEXT

    def _init(self, **kwargs):
        self._clients = {}
        self._SSHClientBaseClass = SSHClientBase

    def _childclass_selector(self, **kwargs):
        """
        gives a creator of a factory the ability to change the type of child to be returned
        :return:
        """
        if "client_type" in kwargs and kwargs["client_type"] == "pssh":
            return SSHClient
        elif j.core.platformtype.myplatform.platform_is_osx:
            # return SSHClientParamiko
            return SSHClient
        else:
            return SSHClient

    def test(self):
        """
        kosmos 'j.clients.ssh.test()'
        """

        # TODO:*1 create docker make sure default key is used in the docker
        # d = j.sal.docker.create(name='test', ports='22:8022', vols='', volsro='', stdout=True, base='phusion/baseimage',
        #                     nameserver=['8.8.8.8'], replace=True, cpu=None, mem=0,
        #                     myinit=True, sharecode=True)

        # TODO: then connect to the just created docker and do some more tests

        # addr = "104.248.87.200"
        # port = 22
        #
        # # make sure we enforce pssh
        # cl = j.clients.ssh.get(name="remote1", addr=addr, port=port, client_type="pssh")

        cl = j.clients.digitalocean.get_testvm_sshclient(delete=False)

        ex = cl.executor

        cl.reset()
        assert ex.state == {}
        assert cl._connected == None
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

        assert e["HOME"] == "/root"

        ex.file_write("/tmp/1", "a")
        assert ex.file_read("/tmp/1").strip() == "a"

        ftp = cl.sftp

        stat = cl.sftp_stat("/tmp/1")
        statdir = cl.sftp_stat("/tmp")
        assert stat.filesize == 1

        assert ex.path_isdir("/tmp")
        assert ex.path_isfile("/tmp") == False
        assert ex.path_isfile("/tmp/1")

        path = ex.download("/tmp/1", "/tmp/something.txt")
        path = ex.upload("/tmp/something.txt", "/tmp/2")

        assert ex.file_read("/tmp/2").strip() == "a"

        assert j.sal.fs.readFile("/tmp/something.txt").strip() == "a"
        j.sal.fs.remove("/tmp/something.txt")

        j.sal.fs.createDir("/tmp/8888")
        j.sal.fs.createDir("/tmp/8888/5")
        j.sal.fs.writeFile("/tmp/8888/1.txt", "a")
        j.sal.fs.writeFile("/tmp/8888/2.txt", "a")
        j.sal.fs.writeFile("/tmp/8888/5/3.txt", "a")

        path = ex.upload("/tmp/8888")

        r = ex.find("/tmp/8888")
        assert r == ["/tmp/8888/1.txt", "/tmp/8888/2.txt", "/tmp/8888/5", "/tmp/8888/5/3.txt"]

        ex.download("/tmp/8888", "/tmp/8889")

        r2 = j.sal.fs.listFilesAndDirsInDir("/tmp/8889")
        r2.sort()
        assert r2 == ["/tmp/8889/1.txt", "/tmp/8889/2.txt", "/tmp/8889/5", "/tmp/8889/5/3.txt"]

        cl.executor.delete("/tmp/8888")
        r2 = ex.find("/tmp/8888")
        assert r2 == []

        j.sal.fs.remove("/tmp/8888")
        j.sal.fs.remove("/tmp/8889")

        cl.reset()
        assert ex.state == {}
        assert cl._connected == None
        assert ex.env_on_system_msgpack == b""
        assert ex.config_msgpack == b""

        self._log_info("TEST FOR SSHCLIENT IS OK")
