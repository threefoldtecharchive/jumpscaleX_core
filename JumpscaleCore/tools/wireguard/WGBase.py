from Jumpscale import j


class WGBase:
    def __init__(self, **kwargs):
        self._ssh = None

    @property
    def islocal(self):
        return self.sshclient_name == ""

    def key_pair_get(self):
        rc, out3, err = self.executor.execute("wg genkey", showout=False)
        privkey2 = out3.strip()
        rc, out4, err = self.executor.execute("echo %s | wg pubkey" % privkey2, showout=False)
        pubkey2 = out4.strip()
        return privkey2, pubkey2

    @property
    def ssh(self):
        if self.islocal:
            raise j.exceptions.Base("cannot do ssh to local machine")
        if not self._ssh:
            self._ssh = j.clients.ssh.get(name=self.sshclient_name, needexist=True)
        return self._ssh

    @property
    def executor(self):
        if self.islocal:
            return j.tools.executorLocal
        else:
            return self.ssh.executor

    def install(self):
        """
        get wireguard to work
        :return:
        """
        # self.executor.uid
        if self.executor.platformtype.platform_is_osx:
            j.sal.process.execute("brew install wireguard-tools")
        else:
            # need to check on ubuntu
            rc, out, err = self.executor.execute("wg", die=False)
            if rc != 0:
                C = """
                add-apt-repository ppa:wireguard/wireguard
                apt-get update
                apt upgrade -y --force-yes
                apt-get install wireguard -y
                """
                self.executor.execute(C)

    def start(self):

        c = "sudo wireguard-go utun9"
