from Jumpscale import j

from .ExecutorBase import ExecutorBase
from .ExecutorSSH import ExecutorSSH
from .ExecutorLocal import ExecutorLocal
from .ExecutorSerial import ExecutorSerial


class ExecutorFactory(j.baseclasses.object_config_collection_testtools):
    _executors = {}
    __jslocation__ = "j.tools.executor"
    _CHILDCLASS = ExecutorBase
    _SCHEMATEXT = _CHILDCLASS._SCHEMATEXT

    def _childclass_selector(self, jsxobject):
        """
        gives a creator of a factory the ability to change the type of child to be returned

        type = "local,ssh,corex,serial" (E)

        :return:
        """
        if jsxobject.type == "local":
            return ExecutorLocal
        elif jsxobject.type == "ssh":
            return ExecutorSSH
        else:
            raise j.exceptions.Base("not implemented yet")

    @property
    def local(self):
        return self.get(name="local", type="local")

    def local_get(self):
        return self.local

    def ssh_get(self, sshclient):
        if j.data.types.string.check(sshclient):
            sshclient = j.clients.ssh.get(name=sshclient)
        # key = "%s:%s:%s" % (sshclient.addr, sshclient.port, sshclient.login)
        return self.get(name="ssh_%s" % sshclient.name, type="ssh", connection_name=sshclient.name)

    #
    # def serial_get(self, device, baudrate=9600, type="serial", parity="N", stopbits=1, bytesize=8, timeout=1):
    #     return ExecutorSerial(
    #         device, baudrate=baudrate, type=type, parity=parity, stopbits=stopbits, bytesize=bytesize, timeout=timeout
    #     )

    def test(self):
        """
        kosmos 'j.tools.executor.test()'
        :return:
        """
        e = j.clients.digitalocean.get_testvm_sshclient(delete=False).executor

        e.state_set("test")

        j.shell()
        w

        e.installer.base()

        j.shell()
