from Jumpscale import j
from .DigitalOcean import DigitalOcean

JSConfigBaseFactory = j.baseclasses.objects_config_bcdb


class DigitalOceanFactory(JSConfigBaseFactory):

    __jslocation__ = "j.clients.digitalocean"
    _CHILDCLASS = DigitalOcean

    def _init(self, **kwargs):
        self.connections = {}

    # def install(self):
    #     try:
    #         import digitalocean
    #     except:
    #         j.builders.runtimes.python.pip_package_install("python-digitalocean")
    #         import digitalocean

    def get_testvm_sshclient(self, delete=False):
        """
        do:
        kosmos 'j.clients.digitalocean.get_testvm_sshclient()'
        """
        if not self.main.token_:
            token = j.tools.console.askString("digital ocean token")
            self.main.token_ = tokengun
            self.main.save()
        c = self.get(name="main")
        if j.clients.ssh.exists("do_test"):
            sshclient = j.clients.ssh.get("do_test")
            rc, out, err = sshclient.execute("ls /", showout=False, die=False)
            if rc > 0:
                droplet, sshclient = c.droplet_create(delete=delete)
        else:
            droplet, sshclient = c.droplet_create(delete=delete)
        return sshclient

    def test(self, reset=False):
        """
        do:
        kosmos 'j.clients.digitalocean.test()'
        """
        j.core.myenv.interactive = True

        from pudb import set_trace

        set_trace()
        if not self.exists(name="main"):
            self.new("main")
        else:
            if reset:
                self.main.delete()
                self.new("main")

        if not self.main.token_:
            print("can get digital ocean token from: ")
            token = j.tools.console.askString("digital ocean token")
            self.main.token_ = token
            self.main.save()

        c = self.get(name="main")

        self._log_info(c.digitalocean_sizes)

        size = "s-6vcpu-16gb"
        # size="s-1vcpu-2gb"

        client = c.client

        droplet, sshclient = c.droplet_create(delete=True, size_slug=size)

        e = sshclient.executor

        e.execute("ls /")

        e.installer.jumpscale_container()

        self._log_info(c.droplets)
        self._log_info(c.digitalocean_images)
        self._log_info(c.digitalocean_regions)
        self._log_info(droplet.ip_address)
