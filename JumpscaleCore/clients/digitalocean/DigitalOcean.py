from Jumpscale import j


try:
    import digitalocean
except:
    j.builders.runtimes.python.pip_package_install("python-digitalocean")
    import digitalocean
from .DigitalOceanVM import DigitalOceanVM


class DigitalOcean(j.baseclasses.object_config):
    _SCHEMATEXT = """
    @url = jumpscale.digitalocean.client
    name* = "" (S)
    token_ = "" (S)
    project_name = "" (S)
    meta = {} (DICT)
    vms = (LO) !jumpscale.digitalocean.vm
        
    @url = jumpscale.digitalocean.vm
    name = "" (S)
    do_id = "" (S)
    meta = {} (DICT)    
    """
    # _CHILDCLASS = DigitalOceanVM

    def _init(self, **kwargs):
        self._client = None
        self.reset()

    def reset(self):
        self._droplets = []
        self._digitalocean_images = None
        self._digitalocean_sizes = None
        self._digitalocean_regions = None
        self._sshkeys = None

    @property
    def client(self):
        """If client not set, a new client is created
        
        :raises RuntimeError: Auth token not configured
        :return: client
        :rtype: 
        """

        if not self._client:
            self._client = digitalocean.Manager(token=self.token_)
        return self._client

    @property
    def digitalocean_images(self):
        if not self._digitalocean_images:
            self._digitalocean_images = self.client.get_distro_images()
        return self._digitalocean_images

    @property
    def digitalocean_myimages(self):
        return self.client.get_images(private=True)

    @property
    def digitalocean_sizes(self):
        if not self._digitalocean_sizes:
            self._digitalocean_sizes = self.client.get_all_sizes()
        return self._digitalocean_sizes

    @property
    def digitalocean_regions(self):
        if not self._digitalocean_regions:
            self._digitalocean_regions = self.client.get_all_regions()
        return self._digitalocean_regions

    @property
    def digitalocean_region_names(self):
        return [i.slug for i in self.digitalocean_regions]

    @property
    def sshkeys(self):
        if not self._sshkeys:
            self._sshkeys = self.client.get_all_sshkeys()
        return self._sshkeys

    def droplet_exists(self, name):
        for droplet in self.droplets:
            if droplet.name.lower() == name.lower():
                return True
        return False

    def _droplet_get(self, name):
        for droplet in self.droplets:
            if droplet.name.lower() == name.lower():
                return droplet
        return False

    def _sshkey_get_default(self):
        sshkey_ = j.clients.sshkey.default
        pubkeyonly = sshkey_.pubkey_only
        for item in self.sshkeys:
            if item.public_key.find(pubkeyonly) != -1:
                return item
        j.shell()
        return None

    def sshkey_get(self, name):
        for item in self.sshkeys:
            if name == item.name:
                return item
        raise j.exceptions.Base("did not find key:%s" % name)

    def region_get(self, name):
        for item in self.digitalocean_regions:
            if name == item.slug:
                return item
            if name == item.name:
                return item
        raise j.exceptions.Base("did not find region:%s" % name)

    @property
    def digitalocean_account_images(self):
        return self.digitalocean_images + self.digitalocean_myimages

    def image_get(self, name):
        for item in self.digitalocean_account_images:
            if item.description:
                name_do = item.description.lower()
            else:
                name_do = item.distribution + " " + item.name
            if name_do.lower().find(name) != -1:
                return item
        raise j.exceptions.Base("did not find image:%s" % name)

    def image_names_get(self, name=""):
        res = []
        name = name.lower()
        for item in self.digitalocean_images:
            if item.description:
                name_do = item.description.lower()
            else:
                name_do = item.distribution + " " + item.name
            if name_do.find(name) != -1:
                res.append(name_do)
        return res

    def droplet_create(
        self, name="test", sshkey=None, region="Amsterdam 3", image="ubuntu 18.04", size_slug="s-1vcpu-2gb", delete=True
    ):
        """

        :param name:
        :param sshkey:
        :param region:
        :param image:
        :param size_slug: s-1vcpu-2gb,s-6vcpu-16gb,gd-8vcpu-32gb
        :param delete:
        :param mosh: when mosh will be used to improve ssh experience
        :return: droplet,sshclient
        """
        if not sshkey:
            sshkey_do = self._sshkey_get_default()
            if not sshkey_do:
                sshkey_ = j.clients.sshkey.default
                # means we did not find the sshkey on digital ocean yet, need to create
                key = digitalocean.SSHKey(token=self.token_, name=sshkey_.name, public_key=sshkey_.pubkey)
                key.create()
            sshkey_do = self._sshkey_get_default()
            assert sshkey_do
            sshkey = sshkey_do.name

        if self.droplet_exists(name):
            dr0 = self._droplet_get(name=name)
            if delete:
                dr0.destroy()
            else:
                sshcl = j.clients.ssh.get(
                    name="do_%s" % name, addr=dr0.ip_address, client_type="pssh", sshkey_name=sshkey
                )
                sshcl.save()
                return dr0, sshcl

        sshkey = self.sshkey_get(sshkey)

        region = self.region_get(region)

        imagedo = self.image_get(image)

        if region.slug not in imagedo.regions:
            j.shell()
        img_slug_or_id = imagedo.slug if imagedo.slug else imagedo.id
        droplet = digitalocean.Droplet(
            token=self.token_,
            name=name,
            region=region.slug,
            image=img_slug_or_id,
            size_slug=size_slug,
            ssh_keys=[sshkey],
            backups=False,
        )
        droplet.create()
        # dr = self.get(name=name)
        # dr.do_id = droplet.id
        self._droplets.append(droplet)
        self.reset()

        vm = self._vm_get(name)
        vm.do_id = droplet.id
        self.save()

        def actions_wait():
            while True:
                actions = droplet.get_actions()
                if len(actions) == 0:
                    return
                for action in actions:
                    action.load()
                    # Once it shows complete, droplet is up and running
                    print(action.status)
                    if action.status == "completed":
                        return

        actions_wait()
        droplet.load()

        sshcl = j.clients.ssh.get(
            name="do_%s" % name, addr=droplet.ip_address, client_type="pssh", sshkey_name=sshkey.name
        )
        sshcl.state_reset()  # important otherwise the state does not correspond
        sshcl.save()

        return droplet, sshcl

    def _vm_get(self, name, new=True):
        vm = None
        for vm in self.vms:
            if vm.name == name:
                break
        if new:
            if not vm:
                vm = self.vms.new()
                vm.name = name
        return vm

    def _vm_exists(self, name):
        return self._vm_get(name, new=False) != None

    def droplet_get(self, name):
        if not self._vm_exists(name):
            raise j.exceptions.Input("could not find vm with name:%s" % name)
        return self._droplet_get(name)

    @property
    def droplets(self):
        if not self._droplets:
            self._droplets = self.client.get_all_droplets()
        return self._droplets

    def droplets_all_delete(self):
        for droplet in self.droplets:
            droplet.destroy()

    def droplets_all_shutdown(self):
        for droplet in self.droplets:
            droplet.shutdown()

    def __str__(self):
        return "digital ocean client:%s" % self.name

    __repr__ = __str__
