from Jumpscale import j

from .ExecutorSSH import ExecutorSSH
from .ExecutorLocal import ExecutorLocal
from .ExecutorSerial import ExecutorSerial

JSBASE = j.baseclasses.object


class ExecutorFactory(j.baseclasses.object):
    _executors = {}
    __jslocation__ = "j.tools.executor"

    @property
    def local(self):
        return self.local_get()

    def local_get(self):
        if "localhost" not in self._executors:
            self._executors["localhost"] = ExecutorLocal()
        return self._executors["localhost"]

    def ssh_get(self, sshclient):
        if j.data.types.string.check(sshclient):
            sshclient = j.clients.ssh.get(name=sshclient)
        key = "%s:%s:%s" % (sshclient.addr, sshclient.port, sshclient.login)
        if key not in self._executors or self._executors[key].sshclient is None:
            self._executors[key] = ExecutorSSH(sshclient=sshclient)
        return self._executors[key]

    def serial_get(self, device, baudrate=9600, type="serial", parity="N", stopbits=1, bytesize=8, timeout=1):
        return ExecutorSerial(
            device, baudrate=baudrate, type=type, parity=parity, stopbits=stopbits, bytesize=bytesize, timeout=timeout
        )

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
