class WireGuardServer:
    """
    the server is over SSH, the one running this tool is the client
    and has access to local machine

    myid is unique id < 200
    the server id is always >200

    myid==199 means we are on local docker

    this is not a full blown client/server implementation for wireguard, its made for 1 server
    which we can access over ssh
    and multiple clients

    """

    def __init__(self, addr=None, port=22, myid=None):
        self._config = None
        assert addr
        self.addr = addr
        self.port = port
        self.port_wireguard = 9001

        if not myid:
            myid = MyEnv.registry.myid

        self.myid = myid
        self.serverid = 201

        assert myid != self.serverid
        assert self.serverid > 200

        self._config_local = None
        self.executor = ExecutorSSH(addr, port)

    def reset(self):
        """
        reset client and server
        """
        self.config["clients"].pop(self.myid)
        self.executor.config.pop("wireguard")
        # now makes sure is all empty on server
        self.executor.save()

    def install(self):
        ubuntu_install = """
            apt-get install software-properties-common -y
            add-apt-repository ppa:wireguard/wireguard
            apt-get update
            apt-get install wireguard -y
            """
        if not Tools.cmd_installed("wg"):
            if MyEnv.platform() == "linux":
                Tools.execute(ubuntu_install)
            elif MyEnv.platform() == "darwin":
                C = "brew install wireguard-tools bash"
                Tools.execute(C)
        if not self.executor.cmd_installed("wg"):
            # only ubuntu for now
            self.executor.execute(ubuntu_install, interactive=True)

    @property
    def config(self):
        c = self.executor.config
        if not "wireguard" in c:
            c["wireguard"] = {}
        wgconfig = self.executor.config["wireguard"]
        if "clients" not in wgconfig:
            wgconfig["clients"] = {}
        if self.myid not in wgconfig["clients"]:
            wgconfig["clients"][self.myid] = {}
        if "server" not in wgconfig:
            wgconfig["server"] = {}
        if "WIREGUARD_PORT" not in wgconfig["server"]:
            wgconfig["server"]["WIREGUARD_PORT"] = self.port_wireguard
            wgconfig["server"]["WIREGUARD_ADDR"] = self.addr
        if "serverid" not in wgconfig["server"]:
            wgconfig["server"]["serverid"] = self.serverid
        return wgconfig

    @property
    def config_server_mine(self):
        return self.config["clients"][self.myid]

    @property
    def config_server(self):
        return self.config["server"]

    @property
    def config_local(self):
        config_local = self.config_server_mine
        if "WIREGUARD_CLIENT_PRIVKEY" not in config_local:
            privkey, pubkey = self.generate_key_pair()
            config_local["WIREGUARD_CLIENT_PUBKEY"] = pubkey
            config_local["WIREGUARD_CLIENT_PRIVKEY"] = privkey
            self.save()
        return config_local

    def save(self):
        """
        everything always stored on server
        """
        self.executor.save()

    def generate_key_pair(self):
        print("- GENERATE WIREGUARD KEY")
        rc, out, err = Tools.execute("wg genkey", showout=False)
        privkey = out.strip()
        rc, out2, err = Tools.execute("echo %s | wg pubkey" % privkey, showout=False)
        pubkey = out2.strip()
        return privkey, pubkey

    def _subnet_calc(self, a):
        """
        go from integer to 2 bytes
        :return:
        """
        import struct

        s = struct.pack(">H", a)
        first, second = struct.unpack(">BB", s)

        return "%s.%s" % (first, second)

    def server_start(self):
        self.install()
        config = self.config["server"]
        if "WIREGUARD_SERVER_PUBKEY" not in config:
            privkey, pubkey = self.generate_key_pair()
            config["WIREGUARD_SERVER_PUBKEY"] = pubkey
            config["WIREGUARD_SERVER_PRIVKEY"] = privkey
            config["SUBNET"] = self._subnet_calc(self.serverid)
            # config["IP_ADDRESS"] = f'10.{config["SUBNET"]}.{ip_last_byte}/24'

        self.config_server_mine["WIREGUARD_CLIENT_PUBKEY"] = self.config_local["WIREGUARD_CLIENT_PUBKEY"]
        self.config_server_mine["SUBNET"] = self._subnet_calc(self.myid)

        self.save()

        C = """
        [Interface]
        Address = 10.{SUBNET}.1/24
        SaveConfig = true
        PrivateKey = {WIREGUARD_SERVER_PRIVKEY}
        ListenPort = {WIREGUARD_PORT}
        """
        C = Tools.text_replace(C, args=config, die_if_args_left=True)

        for client_id, client in self.config["clients"].items():

            C2 = """

            [Peer]
            PublicKey = {WIREGUARD_CLIENT_PUBKEY}
            AllowedIPs = 10.{SUBNET}.0/24
            """
            C2 = Tools.text_replace(C2, args=client, die_if_args_left=True)
            C += C2

        path = "/etc/wireguard/wg0.conf"
        self.executor.file_write(path, C, mode="0600")
        rc, out, err = self.executor.execute("ip link del dev wg0", showout=False, die=False)
        # cmd = "wg-quick down %s" % path #DONT DO BECAUSE OVERWRITES CONFIG
        # self.executor.execute(cmd)
        cmd = "wg-quick up %s" % path
        self.executor.execute(cmd)

    def connect(self):

        C = """
        [Interface]
        Address = 10.{SUBNET}.2/24
        PrivateKey = {WIREGUARD_CLIENT_PRIVKEY}
        """
        self.config_local["SUBNET"] = self._subnet_calc(self.myid)
        C = Tools.text_replace(C, args=self.config_local)
        C2 = """

        [Peer]
        PublicKey = {WIREGUARD_SERVER_PUBKEY}
        Endpoint = {WIREGUARD_ADDR}:{WIREGUARD_PORT}
        AllowedIPs = 10.{SUBNET}.0/24
        AllowedIPs = 172.17.0.0/16
        PersistentKeepalive = 25
        """
        C2 = Tools.text_replace(C2, args=self.config_server)
        C += C2
        Tools.file_write(self.config_path_client, C)
        self.disconnect()
        if MyEnv.platform() == "linux":
            cmd = "/usr/local/bin/bash /usr/local/bin/wg-quick up %s" % self.config_path_client
            Tools.execute(cmd)
            Tools.shell()
        else:
            cmd = "/usr/local/bin/bash /usr/local/bin/wg-quick up %s" % self.config_path_client
            print(cmd)
            Tools.execute(cmd)

    @property
    def config_path_client(self):
        path = "{DIR_BASE}/cfg/wireguard/%s/wg0.conf" % self.serverid
        path = Tools.text_replace(path)
        Tools.dir_ensure(os.path.dirname(path))
        return path

    def disconnect(self):
        """
        stop the client
        """
        if MyEnv.platform() == "linux":
            rc, out, err = Tools.execute("ip link del dev wg0", showout=False, die=False)
        else:
            cmd = "/usr/local/bin/bash /usr/local/bin/wg-quick down %s" % self.config_path_client
            Tools.execute(cmd, die=False, showout=True)

    @property
    def config_file_server(self):
        path = "/etc/wireguard/wg0.conf"
        return str(self.executor.file_read(path))

    @property
    def config_file_client(self):
        path = "{DIR_BASE}/cfg/wireguard/%s/wg0.conf" % self.serverid
        path = Tools.text_replace(path)

        return str(Tools.file_read(path).decode())

    def __repr__(self):
        out = ""
        out += self.config_file_server
        out += "\n\n====================================CLIENT======================\n"
        out += self.config_file_client
        return out

    __str__ = __repr__
