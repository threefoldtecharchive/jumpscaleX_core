from Jumpscale import j
import ovh

import requests
import time

JSConfigBase = j.baseclasses.object_config


class OVHClient(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.ovh.client
    name* = "" (S)
    ipxeBase = "https://bootstrap.grid.tf/ipxe/master" (S)
    endpoint = "soyoustart-eu" (S)
    appkey_ = "" (S)
    appsecret_ = "" (S)
    consumerkey_ = "" (S)
    """

    def _init(self, **kwargs):

        # id = "ovhclient_%s" % c["consumerkey_"]

        self._connect()

        self.client.get("/me")

        if self.consumerkey_ == "":
            self.consumer_key_get()
            self._connect()

        self.client.get("/me")

    def consumer_key_get(self):
        # TODO:*1 something still goes wrong here, need to debug
        ck = self.client.new_consumer_key_request()
        ck.add_recursive_rules(ovh.API_READ_WRITE, "/")
        # ck.add_rules(["GET", "POST", "PUT", "DELETE"], "/*")
        validation = ck.request()
        self._log_info(validation["consumerKey"])
        self.consumerkey_ = validation["consumerKey"]
        self.save

    def _connect(self):
        self.client = ovh.Client(
            endpoint=self.endpoint,
            application_key=self.appkey_,
            application_secret=self.appsecret_,
            consumer_key=self.consumerkey_,
        )
        self.ipxeBase = self.ipxeBase

    def ovh_id_check(self, ovh_id):
        if "ns302912" in ovh_id:
            raise j.exceptions.Base("Cannot use server:%s" % ovh_id)

    def reset(self):
        """
        resets cache
        """
        self._cache.reset()

    def installationtemplates_get(self):
        """
        gets installation templates
        """

        def getData():
            self._log_debug("get installationtemplates_get")
            return self.client.get("/dedicated/installationTemplate")

        return self._cache.get("installationtemplates_get", getData, expire=3600)

    def sshkeys_get(self):
        """
        lists ssh keys in server
        """

        def getData():
            self._log_debug("get sshkeys")
            return self.client.get("/me/sshKey")

        return self._cache.get("sshKeys", getData)

    def sshkey_add(self, name, key):
        """ adds a ssh key to the server
        @param name: name of the new public SSH key
        @param key: ASCII encoded public SSH key to add
        """
        return self.client.post("/me/sshKey", keyName=name, key=key)

    def node_get(self, name):
        """
        get node by name
        """
        return j.tools.nodemgr.get(name, create=False)

    def servers_list(self):
        """
        list servers
        """

        def getData():
            self._log_debug("get serversList")
            llist = self.client.get("/dedicated/server")
            llist = [item for item in llist if item.find("ns302912") == -1]
            return llist

        return self._cache.get("serversList", getData)

    def server_detail_get(self, name, reload=False):
        """
        get server details
        @param name: server name
        @param reload: if True the cache will be deleted and will the updated details
        """
        self.ovh_id_check(name)
        key = "server_detail_get_%s" % name
        if reload:
            self._cache.delete(key)

        def getData(name):
            return self.client.get("/dedicated/server/%s" % name)

        return self._cache.get(key, getData, name=name, expire=120)

    def server_install_status(self, name, reload=False):
        """
        get server install details
        @param name: server name
        @param reload: if True the cache will be deleted and will the updated details
        """
        self.ovh_id_check(name)
        key = "serverGetInstallStatus%s" % name
        if reload:
            self._cache.delete(key)

        def getData(name):
            self._log_debug("get %s" % key)
            try:
                return self.client.get("/dedicated/server/%s/install/status" % name)
            except Exception as e:
                if "Server is not being installed or reinstalled at the moment" in str(e):
                    return "active"
                else:
                    raise e

        return self._cache.get(key, getData, name=name, expire=120)

    def servers_detail_get(self):
        """
        get details for all servers in self.servers_list()
        """
        res = []
        for item in self.servers_list():
            res.append((item, self.server_detail_get(item)))
        return res

    def servers_install_wait(self):
        nrInstalling = 1
        while nrInstalling > 0:
            nrInstalling = 0
            for item in self.servers_list():
                status = self.server_install_status(name=item, reload=True)
                key = "server_detail_get_%s" % item  # lets make sure server is out of cache too
                self._cache.delete(key)
                if status != "active":
                    self._log_debug(item)
                    self._log_debug(j.data.serializers.yaml.dumps(status))
                    self._log_debug("-------------")
                    nrInstalling += 1
            time.sleep(2)
        self.details = {}
        self._log_info("server install done")

    def server_install(
        self,
        name,
        ovh_id,
        installationTemplate="ubuntu1710-server_64",
        sshKeyName=None,
        useDistribKernel=True,
        noRaid=True,
        hostname="",
        wait=True,
    ):
        """

        if sshKeyName == None, and there is only 1 loaded, then will take that key

        will return node_client

        """
        if name == "" or name is None:
            raise j.exceptions.Input(message="please specify name")

        if ovh_id == "" or ovh_id is None:
            raise j.exceptions.Input(message="please specify ovh_id")

        self.ovh_id_check(ovh_id)
        if installationTemplate not in self.installationtemplates_get():
            raise j.exceptions.Input(message="could not find install template:%s" % name)

        if sshKeyName == None:
            items = j.clients.sshkey.list()
            # if len(items) != 1:
            #     raise j.exceptions.Base(
            #         "sshkeyname needs to be specified or only 1 sshkey needs to be loaded")
            sshKeyName = items[0]
            sshKeyName = j.sal.fs.getBaseName(sshKeyName)

        if sshKeyName not in self.sshkeys_get():
            pubkey = j.clients.ssh.sshkey_pub_get(sshKeyName)
            self.sshkey_add(sshKeyName, pubkey)

        if hostname == "":
            hostname = name

        details = {}
        details["installationTemplate"] = installationTemplate
        details["useDistribKernel"] = useDistribKernel
        details["noRaid"] = noRaid
        details["customHostname"] = hostname
        details["sshKeyName"] = sshKeyName

        # make sure cache for this server is gone
        key = "server_detail_get_%s" % name
        self._cache.delete(key)

        try:
            self.client.post(
                "/dedicated/server/%s/install/start" % ovh_id, details=details, templateName=installationTemplate
            )
        except Exception as e:
            if "A reinstallation is already in todo" in str(e):
                self._log_debug("%s:%s" % (name, e))
                pass
            else:
                raise e

        if wait:
            self.servers_install_wait()

        if name == "":
            self.details = {}
        else:
            if name in self.details:
                self.details.pop(name)

        conf = self.server_detail_get(ovh_id)
        ipaddr = conf["ip"]
        port = 22

        node = j.tools.nodemgr.set(name, ipaddr, port, sshclient=sshKeyName, cat="ovh", clienttype="j.clients.ovh")

        j.tools.executor.reset()

        return node

    def boot_image_pxe_list(self):
        """
        Lists iPXE scripts installed on the account
        """
        return self.client.get("/me/ipxeScript")

    def boot_image_pxe_get(self, name):
        """
        Returns contents of the iPXE script name given in parameter
        """
        return self.client.get("/me/ipxeScript/%s" % name)

    def boot_image_pxe_delete(self, name):
        """
        Delete a iPXE script boot entry
        Note: this require DELETE account capability
        """
        return self.client.delete("/me/ipxeScript/%s" % name)

    def boot_image_pxe_set(self, name, script, description=""):
        """
        Set a new iPXE boot script bootloader
        ipxe: should contains a dictionary with:
          - description: a description which will be displayed on the summary page
          - name: a name which will identify the iPXE script entry
          - script: the iPXE script which will be executed during the boot
        """
        dd = {}
        dd["name"] = name
        dd["script"] = script
        dd["description"] = description

        return self.client.post("/me/ipxeScript", **dd)

    def boot_image_pxe_available(self, name):
        """
        Checkk if an iPXE boot script name already exists
        """
        existing = self.boot_image_pxe_list()

        for item in existing:
            if item == name:
                return True

        return None

    def _bootloader_set(self, target, bootid):
        self._log_info("[+] bootloader selected: %s" % bootid)

        payload = {"bootId": int(bootid)}
        self.client.put("/dedicated/server/%s" % target, **payload)

        return True

    def bootloader_set(self, target, name):
        """
        Set and apply an iPXE boot script to a remote server
        - target: need to be a OVH server hostname
        - name: need to be an existing iPXE script name
        """
        bootlist = self.client.get("/dedicated/server/%s/boot?bootType=ipxeCustomerScript" % target)
        # checked = None

        for bootid in bootlist:
            data = self.client.get("/dedicated/server/%s/boot/%s" % (target, bootid))
            if data["kernel"] == name:
                return self._bootloader_set(target, bootid)

        return False

    def server_reboot(self, name):
        """
        Reboot a server
        - target: need to be a OVH server hostname
        """
        self.ovh_id_check(name)
        return self.client.post("/dedicated/server/%s/reboot" % name)

    #
    # custom builder
    #
    def _zos_build(self, url):
        """
        Internal use.
        This build an OVH adapted iPXE script based on an official bootstrap URL
        """
        # strip trailing flash
        url = url.rstrip("/")
        self._log_info("zero hub url:%s" % url)
        # downloading original ipxe script
        try:
            script = requests.get(url)
        except Exception as e:
            msg = "ERROR: zerohub server does not respond\nError:\n%s\n" % e
            raise (msg)
        if script.status_code != 200:
            raise j.exceptions.Base("Invalid script URL")

        # going unsecure, because ovh
        fixed = script.text.replace("https://bootstrap.", "http://unsecure.bootstrap.")

        # setting name and description according to the url
        fields = url.split("/")

        if len(fields) == 7:
            # branch name, zerotier network, arguments
            description = "Zero-OS: %s (%s, %s)" % (fields[4], fields[5], fields[6])
            name = "zero-os-%s-%s,%s" % (fields[4], fields[5], fields[6])

        elif len(fields) == 6:
            # branch name, zerotier network, no arguments
            description = "Zero-OS: %s (%s, no arguments)" % (fields[4], fields[5])
            name = "zero-os-%s-%s" % (fields[4], fields[5])

        else:
            # branch name, no zerotier, no arguments
            description = "Zero-OS: %s (no zerotier, no arguments)" % fields[4]
            name = "zero-os-%s" % fields[4]

        return {"description": description, "name": name, "script": fixed}

    def zero_os_boot(self, target, zerotierNetworkID):
        """
        Configure a node to use Zero-OS iPXE kernel
        - target: need to be an OVH server hostname
        - zerotierNetworkID: network to be used in zerotier
        """
        self.ovh_id_check(target)
        url = "%s/%s" % (self.ipxeBase, zerotierNetworkID)
        ipxe = self._zos_build(url)

        self._log_info("[+] description: %s" % ipxe["description"])
        self._log_info("[+] boot loader: %s" % ipxe["name"])

        if not self.boot_image_pxe_available(ipxe["name"]):
            self._log_info("[+] installing the bootloader")
            self.boot_image_pxe_set(ipxe["name"], ipxe["script"], ipxe["description"])
        self.bootloader_set(target, ipxe["name"])
        return self.server_reboot(target)

    def task_get(self, target, taskId):
        """
        get a task
        @param target: target name
        @param taskId: taskId
        """
        return self.client.get("/dedicated/server/%s/task/%s" % (target, taskId))

    def server_wait_reboot(self, target, taskId):
        current = ""

        while True:
            status = self.task_get(target, taskId)

            if status["status"] != current:
                current = status["status"]
                self._log_info("[+] rebooting %s: %s" % (target, current))

            if status["status"] == "done":
                return True

            time.sleep(1)

    #

    # IS THIS STILL RELEVANT

    # def zero_node_ovh_install(self, OVHHostName, OVHClient, zerotierNetworkID, zerotierClient):
    #     """
    #
    #     OVHHostName is server name as known by OVH
    #
    #     get clients as follows:
    #     - zerotierClient = j.clients.zerotier.get(instance='main', data={'data': ZT_API_TOKEN})
    #     - OVHClient = j.clients.ovh.get(...)
    #
    #     """
    #
    #     cl = OVHClient
    #
    #     self._log_debug("booting server {} to zero-os".format(OVHHostName))
    #     task = cl.zero_os_boot(target=OVHHostName, zerotierNetworkID=zerotierNetworkID)
    #     self._log_debug("waiting for {} to reboote".format(OVHHostName))
    #     cl.server_wait_reboot(OVHHostName, task['taskId'])
    #     ip_pub = cl.server_detail_get(OVHHostName)["ip"]
    #     self._log_info("ip addr is:%s" % ip_pub)
    #
    #     while True:
    #         try:
    #             network = zerotierClient.get_network(network_id=zerotierNetworkID)
    #             member = network.member_get(public_ip=ip_pub)
    #             ipaddr_priv = member.private_ip
    #             break
    #         except RuntimeError as e:
    #             # case where we don't find the member in zerotier
    #             self._log_error(e)
    #             time.sleep(1)
    #         except IndexError as e:
    #             # case were we the member doesn't have a private ip
    #             self._log_error("please authorize the server with the public ip %s in the zerotier network" % ip_pub)
    #             time.sleep(1)
    #
    #     self._log_debug("server found: %s" % member['id'])
    #     self._log_debug("zerotier IP: %s" % ipaddr_priv)
    #
    #     return ip_pub, ipaddr_priv
