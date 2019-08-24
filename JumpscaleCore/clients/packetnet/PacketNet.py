from Jumpscale import j

import packet
import time

JSConfigBase = j.baseclasses.object_config


class PacketNet(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.packetnet.client
    name* = "" (S)
    auth_token_ = "" (S)
    project_name = "" (S)
    """

    def _init(self, **kwargs):
        self._client = None
        self._plans = None
        self._facilities = None
        self._oses = None
        self._projects = None
        self._projectid = None
        self._devices = None
        self.project_name = self.project_name

    @property
    def client(self):
        """If client not set, a new client is created
        
        :raises RuntimeError: Auth token not configured
        :return: client
        :rtype: 
        """

        if not self._client:
            if not self.auth_token_:
                raise j.exceptions.Base(
                    "please configure your auth_token, do: 'js_config configure -l j.clients.packetnet -i {}'".format(
                        self.name
                    )
                )
            self._client = packet.Manager(auth_token=self.auth_token_)
        return self._client

    @property
    def projectid(self):
        """
        :raises RuntimeError: Project with project_name not found
        :raises RuntimeError: More than one project found
        :return: project id
        :rtype: str
        """

        if self._projectid is None:
            if self.project_name is not "":
                for item in self.projects:
                    if item.name == self.project_name:
                        self._projectid = item.id
                        return self._projectid
                raise j.exceptions.Base("did not find project with name:%s" % self.project_name)
            else:
                res = [item[0] for key, item in self.getProjects().items()]
                if len(res) == 1:
                    self._projectid = res[0]
                else:
                    raise j.exceptions.Base("found more than 1 project")
        return self._projectid

    @property
    def plans(self):
        """
        :return: plans
        :rtype: list
        """

        if self._plans is None:
            self._plans = self.client.list_plans()
            self._log_debug("plans:%s" % self._plans)
        return self._plans

    @property
    def facilities(self):
        """
        :return: facilities
        :rtype: list
        """

        if self._facilities is None:
            self._facilities = self.client.list_facilities()
            self._log_debug("facilities:%s" % self._facilities)
        return self._facilities

    @property
    def operatingsystems(self):
        """
        :return: operatin systems
        :rtype: list
        """

        if self._oses is None:
            self._oses = self.client.list_operating_systems()
            self._log_debug("operatingsystems:%s" % self._oses)
        return self._oses

    @property
    def projects(self):
        """
        :return: projects
        :rtype: list
        """

        if self._projects is None:
            self._projects = self.client.list_projects()
            self._log_debug("projects:%s" % self._projects)
        return self._projects

    @property
    def devices(self):
        """
        :return: devices
        :rtype: list
        """

        if self._devices is None:
            self._devices = self.client.list_devices(self.projectid)
            self._log_debug("devices:%s" % self._devices)
        return self._devices

    def getPlans(self):
        """List all services plans available to provision device on

        :return: plans
        :rtype: dict
        """

        res = {}
        for plan in self.plans:
            res[plan.slug] = (plan.name, plan.specs)
        return res

    def getFacilities(self):
        """List all datacenters/facilities for the given project

        :return: facilities and their locations
        :rtype: dict
        """
        res = {}
        for item in self.facilities:
            res[item.code] = item.name
        return res

    def getOperatingSystems(self):
        """List available operating systems

        :return: operating systems
        :rtype: dict
        """
        res = {}
        for item in self.operatingsystems:
            res[item.slug] = (item.name, item.distro, item.version, item.provisionable_on)
        return res

    def getProjects(self):
        """List projects
        
        :return: projects
        :rtype: dict
        """

        res = {}
        for item in self.projects:
            res[item.name] = (item.id, item.devices)
        return res

    def getDevices(self):
        """List devices for project
        
        :return: devices
        :rtype: dict
        """

        res = {}
        for item in self.devices:
            res[item.hostname] = item
        return res

    def getDevice(self, name, id=None, die=False):
        """Get specific device
        
        :param name: device name
        :type name: str
        :param id:device id, defaults to None
        :type id: str, optional
        :param die: return None if no device was found, defaults to False
        :type die: bool, optional
        :raises RuntimeError: Device not found
        :return: device
        :rtype: dict
        """

        if id is None:
            if name in [item for item in self.getDevices()]:
                return self.getDevices()[name]
            if die is False:
                return None
        else:
            return self.client.get_device(id)

        raise j.exceptions.Base("could not find device:%s" % name)

    def removeDevice(self, name):
        """Remove a specific device
        
        :param name: device name
        :type name: str
        """

        res = self.getDevice(name)
        if res is not None:
            self._devices = None
            self._log_debug("found machine, remove:%s" % name)
            res.delete()
        # j.tools.nodemgr.delete(instance=name)

    def startDevice(
        self,
        hostname="removeMe",
        plan="baremetal_0",
        facility="ams1",
        os="ubuntu_17_04",
        ipxeUrl=None,
        wait=True,
        remove=False,
        sshkey="",
    ):
        """
        will delete if it exists when remove=True, otherwise will check if it exists, if yes will return device object
        if not will create
        example ipxeUrl = https://bootstrap.grid.tf/ipxe/zero-os-master-generic

        :param hostname: name of host, defaults to "removeMe"
        :type hostname: str, optional
        :param plan: plan,  defaults to 'baremetal_0'
        :type plan: str, optional
        :param facility: facility of the project, defaults to 'ams1'
        :type facility: str, optional
        :param os: operating system, defaults to 'ubuntu_17_04'
        :type os: str, optional
        :param ipxeUrl: Url, defaults to None
        :type ipxeUrl: str, optional
        :param wait: defaults to True
        :type wait: bool, optional
        :param remove: defaults to False
        :type remove: bool, optional
        :param sshkey: defaults to ""
        :type sshkey: str, optional
        :return: device object if created
        :rtype: Object
        """

        self._log_info("start device:%s plan:%s os:%s facility:%s wait:%s" % (hostname, plan, os, facility, wait))
        if ipxeUrl is None:
            zerotierId = ""
        else:
            zerotierId = ipxeUrl.split("/")[-1]
        return self._startDevice(
            hostname=hostname,
            plan=plan,
            facility=facility,
            os=os,
            wait=wait,
            remove=remove,
            ipxeUrl=ipxeUrl,
            zerotierId=zerotierId,
            always_pxe=False,
            sshkey=sshkey,
        )

    def startZeroOS(
        self,
        hostname="removeMe",
        plan="baremetal_0",
        facility="ams1",
        zerotierId="",
        zerotierAPI="",
        wait=True,
        remove=False,
        params=None,
        branch="master",
    ):
        """
        return (zero-os-client,pubIpAddress,zerotierIpAddress)

        :param hostname: defaults to "removeMe"
        :type hostname: str, optional
        :param plan: defaults to 'baremetal_0'
        :type plan: str, optional
        :param facility:  facility of the project, defaults to 'ams1'
        :type facility: str, optional
        :param zerotierId: defaults to ""
        :type zerotierId: str, optional
        :param zerotierAPI: defaults to ""
        :type zerotierAPI: str, optional
        :param wait: defaults to True
        :type wait: bool, optional
        :param remove: defaults to False
        :type remove: bool, optional
        :param params: defaults to None
        :type params: [type], optional
        :param branch: defaults to 'master'
        :type branch: str, optional
        :raises RuntimeError: zerotierId not specified
        :raises RuntimeError: zerotierAPI not specified
        :return: zero-os-client, pubIpAddress, zerotierIpAddress
        :rtype: ,str,str
        """
        self._log_info(
            "start device:%s plan:%s facility:%s zerotierId:%s wait:%s" % (hostname, plan, facility, zerotierId, wait)
        )
        if zerotierId.strip() == "" or zerotierId is None:
            raise j.exceptions.Base("zerotierId needs to be specified")
        if zerotierAPI.strip() == "" or zerotierAPI is None:
            raise j.exceptions.Base("zerotierAPI needs to be specified")
        ipxeUrl = "http://unsecure.bootstrap.grid.tf/ipxe/{}/{}".format(branch, zerotierId)

        if params is not None:
            pstring = "%20".join(params)
            ipxeUrl = ipxeUrl + "/" + pstring

        node = self._startDevice(
            hostname=hostname,
            plan=plan,
            facility=facility,
            os="",
            wait=wait,
            remove=remove,
            ipxeUrl=ipxeUrl,
            zerotierId=zerotierId,
            always_pxe=True,
        )

        # data = {'token_': zerotierAPI, 'networkID_': zerotierId}
        data = {"token_": zerotierAPI}
        zerotierClient = j.clients.zerotier.get(self.instance, data=data)

        public_ip = node.addr
        if not public_ip:
            ipaddr = [
                netinfo["address"]
                for netinfo in node.pubconfig["netinfo"]
                if netinfo["public"] and netinfo["address_family"] == 4
            ]
            public_ip = ipaddr[0]

        while True:
            try:
                network = zerotierClient.network_get(network_id=zerotierId)
                member = network.member_get(public_ip=public_ip)
                member.authorize()
                ipaddr_priv = member.private_ip
                break
            except RuntimeError as e:
                # case where we don't find the member in zerotier
                self._log_info("[-] %s" % e)
                time.sleep(5)

        self._log_info("[+] zerotier IP: %s" % ipaddr_priv)
        data = {"host": ipaddr_priv, "timeout": 10, "port": 6379, "password_": "", "db": 0, "ssl": True}
        zosclient = j.clients.zero_os.get(ipaddr_priv, data=data)
        return zosclient, node, ipaddr_priv

    # TODO: IS THIS STILL RELEVANT?

    # def zero_node_packetnet_install(self, packetnetClient, zerotierClient, project_name,
    #                                   plan_type, location, server_name, zerotierNetworkID, ipxe_base='https://bootstrap.grid.tf/ipxe/master'):
    #       """
    #       packetnetClient = j.clients.packetnet.get('TOKEN')
    #       zerotierClient = j.clients.zerotier.get(instance='main', data={'token': 'TOKEN'})
    #       project_name = packet.net project
    #       plan_type: one of "Type 0", "Type 1", "Type 2" ,"Type 2A", "Type 3", "Type S"
    #       location: one of "Amsterdam", "Tokyo", "Synnuvale", "Parsippany"
    #       server_name: name of the server that is going to be created
    #       zerotierNetworkID: zertotier network id
    #       ipxe_base: change this to the version you want, use master branch by default
    #       """
    #
    #       valid_plan_types = ("Type 0", "Type 1", "Type 2",
    #                           "Type 2A", "Type 3", "Type S")  # FIXME
    #       if plan_type not in valid_plan_types:
    #           j.exceptions.Input("bad plan type %s. Valid plan type are %s" % (
    #               plan_type, ','.join(valid_plan_types)))
    #
    #       if zerotierNetworkID:
    #           ipxe_url = "%s/%s" % (ipxe_base, zerotierNetworkID)
    #       else:
    #           ipxe_url = None
    #
    #       hostname = server_name
    #
    #       # find project id
    #       project_ids = [project.id for project in packetnetClient.projects if project.name == project_name]
    #       if not project_ids:
    #           raise j.exceptions.NotFound(
    #               'No projects found with name %s' % project_name)
    #       project_id = project_ids[0]
    #       packetnetClient.project_id = project_id
    #
    #       packetnetClient.startDevice(hostname=server_name, plan=plan_type, facility=location, os='ubuntu_17_04',
    #                                   ipxeUrl=ipxe_url, wait=True, remove=False)
    #
    #       device = packetnetClient.getDevice(server_name)
    #       ip_pub = [netinfo['address'] for netinfo in device.ip_addresses if netinfo['public'] and netinfo['address_family'] == 4]
    #
    #       while True:
    #           try:
    #               network = zerotierClient.get_network(network_id=zerotierNetworkID)
    #               member = network.member_get(public_ip=ip_pub[0])
    #               ipaddr_priv = member.private_ip
    #               break
    #           except RuntimeError as e:
    #               # case where we don't find the member in zerotier
    #               self._log_error(e)
    #               time.sleep(1)
    #           except IndexError as e:
    #               # case were we the member doesn't have a private ip
    #               self._log_error("please authorize the server with the public ip %s in the zerotier network" % ip_pub[0])
    #               time.sleep(1)
    #
    #       self._log_debug("server found: %s" % device.id)
    #       self._log_debug("zerotier IP: %s" % ipaddr_priv)
    #
    #       return ip_pub, ipaddr_priv
    #

    def _startDevice(
        self,
        hostname="removeMe",
        plan="baremetal_0",
        facility="ams1",
        os="ubuntu_17_04",
        wait=True,
        remove=True,
        ipxeUrl=None,
        zerotierId="",
        always_pxe=False,
        sshkey="",
    ):
        """
        will delete if it exists when remove=True, otherwise will check if it exists, if yes will return device object
        if not will create

        example ipxeUrl = https://bootstrap.grid.tf/ipxe/zero-os-master-generic
        """

        if ipxeUrl is None:
            ipxeUrl = ""
        if remove:
            self.removeDevice(hostname)

        if sshkey:
            sshkey = j.clients.sshkey.get(instance=sshkey)

        device = self.getDevice(hostname, die=False)
        if device is None:
            if sshkey:
                self.addSSHKey(sshkey, hostname)

            device = self.client.create_device(
                project_id=self.projectid,
                hostname=hostname,
                plan=plan,
                facility=facility,
                operating_system=os,
                ipxe_script_url=ipxeUrl,
                always_pxe=False,
            )
            self._devices = None

        res = device.update()
        while res["state"] not in ["active"]:
            res = device.update()
            time.sleep(1)
            self._log_debug(res["state"])

        ipaddr = [
            netinfo["address"]
            for netinfo in res["ip_addresses"]
            if netinfo["public"] and netinfo["address_family"] == 4
        ]

        ipaddr = ipaddr[0]

        self._log_info("ipaddress found = %s" % ipaddr)

        sshinstance = ""
        if zerotierId == "":
            j.sal.nettools.waitConnectionTest(ipaddr, 22, 60)

            if not sshkey:
                sshclient = j.clients.ssh.new(instance=hostname, addr=ipaddr)
            else:
                self.addSSHKey(sshkey, hostname)
                sshclient = j.clients.ssh.get(
                    instance=sshkey.instance, data={"addr": ipaddr, "login": "root", "sshkey": sshkey.instance}
                )
            sshclient.connect()
            sshinstance = sshclient.instance

        conf = {}
        conf["facility"] = facility
        conf["netinfo"] = res["ip_addresses"]
        conf["plan"] = plan
        conf["hostname"] = hostname
        conf["project_id"] = self.projectid
        conf["os"] = os
        conf["ipxeUrl"] = ipxeUrl

        sshclient.state_reset()

        j.shell()

        return node

    def addSSHKey(self, sshkey, label):
        if j.data.types.string.check(sshkey):
            sshkey = j.clients.sshkey.get(instance=sshkey)

        ssh_keys = self.client.list_ssh_keys()
        for ssh_key in ssh_keys:
            if ssh_key.key == sshkey.pubkey:
                return ssh_key.owner

        self.client.create_ssh_key(label, sshkey.pubkey)
