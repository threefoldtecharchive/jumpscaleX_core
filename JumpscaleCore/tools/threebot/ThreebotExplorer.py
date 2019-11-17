from Jumpscale import j
from io import BytesIO
import binascii


class ThreebotExplorer(j.baseclasses.object):
    """
    represents connection to the explorer on the threebot network
    """

    def _init(self, **kwargs):
        ## Load and get reservation model
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/tfgrid_workloads/models"
        )

    @property
    def _client(self):
        return j.clients.threebot.explorer

    @property
    def _redis(self):
        return j.clients.threebot.explorer_redis

    @property
    def actors(self):
        return self._client.actors_default

    def threebot_record_get(self, tid=None, name=None, die=True):
        """
        j.tools.threebot.explorer.threebot_record_get(name="something.something",die=False)
        :param tid: threebot id
        :param name: name of your threebot
        :param die:

        if data found will be verified on validity

        :return: a jsxobject which represents a threebot record

        """
        # did not find locally yet lets fetch
        r = self.actors.phonebook.get(tid=tid, name=name, die=die)
        if not die and not r.signature:
            return None
        if r and r.name != "":
            # this checks that the data we got is valid
            rc = j.data.nacl.payload_verify(
                r.id,
                r.name,
                r.email,
                r.ipaddr,
                r.description,
                r.pubkey,
                verifykey=r.pubkey,
                signature=r.signature,
                die=False,
            )
            if not rc:
                raise j.exceptions.Input("threebot record, not valid, signature does not match")

            return r

        if die:
            raise j.exceptions.Input("could not find 3bot: user_id:{user_id} name:{name}")

    def threebot_network_prepay_wallet_create(self, name):
        """

        the threebot will create a wallet for you as a user and you can leave money on there to be used for
        paying micro payment services on the threefold network (maximum amount is 1000 TFT on the wallet)
        THIS IS A WALLET MEANT FOR MICRO PAYMENTS ON THE NETWORK OF THE CORE NETWORK ITSELF !!!
        ITS AN ADVANCE ON SERVICES WHICH WILL BE USED E.G. REGISTER NAMES or NAME RECORDS

        if a wallet stays empty during 1 day it will be removed automatically

        :param: name is the name of the 3bot like how will be used in following functions like threebot_register_name
        :param: sender_signature_hex off the name as done by private key of the person who asks

        :return: a TFT wallet address
        """
        self._log_info("register step0: create your wallet under the name of your main threebot: %s" % name)
        data_return_json = self._redis.execute_command(
            "default.phonebook.wallet_create", j.data.serializers.json.dumps({"name": name})
        )
        data_return = j.data.serializers.json.loads(data_return_json)
        return data_return["wallet_addr"]

    def threebot_register(self, name=None, ipaddr=None, email="", description="", wallet_name=None, nacl=None):
        """

        The cost is 20 TFT today to register a name which is valid for 1 Y.

        :param: name you want to register can eg $name.$extension of $name if no extension will be $name.3bot
                needs to correspond on the name as used in threebot_wallet_create
        :param: wallet_name is the name of a wallet you have funded, by default the same as your name you register
        :param email:
        :param ipaddr:
        :param description:
        :param nacl is the nacl instance you use default self.default which is for the local threebot
        :return: JSX client to the threebot
        """
        assert name

        if not nacl:
            nacl = j.data.nacl.default
        pubkey = nacl.verify_key_hex

        self._log_info("register step1: for 3bot name: %s" % name)
        if not wallet_name:
            wallet_name = name

        data_return_json = self._redis.execute_command(
            "default.phonebook.name_register",
            j.data.serializers.json.dumps({"name": name, "wallet_name": wallet_name, "pubkey": pubkey}),
        )

        data_return = j.data.serializers.json.loads(data_return_json)

        tid = data_return["id"]

        self._log_info("register: {id}:{name} {email} {ipaddr}".format(**data_return))

        # we choose to implement it low level using redis interface
        assert name
        assert tid
        assert isinstance(tid, int)

        data = {
            "tid": tid,
            "name": name,
            "email": email,
            "ipaddr": ipaddr,
            "description": description,
            "pubkey": pubkey,
        }

        def sign(nacl, *args):
            buffer = BytesIO()
            for item in args:
                if isinstance(item, str):
                    item = item.encode()
                elif isinstance(item, int):
                    item = str(item).encode()
                elif isinstance(item, bytes):
                    pass
                else:
                    raise RuntimeError()
                buffer.write(item)
            payload = buffer.getvalue()
            signature = nacl.sign(payload)
            return binascii.hexlify(signature).decode()

        # we sign the different records to come up with the right 'sender_signature_hex'
        sender_signature_hex = sign(
            nacl, data["tid"], data["name"], data["email"], data["ipaddr"], data["description"], data["pubkey"]
        )
        data["sender_signature_hex"] = sender_signature_hex
        data2 = j.data.serializers.json.dumps(data)
        data_return_json = self._redis.execute_command("default.phonebook.record_register", data2)
        data_return = j.data.serializers.json.loads(data_return_json)

        record0 = self.threebot_record_get(tid=data_return["id"])
        record1 = self.threebot_record_get(name=data_return["name"])

        assert record0 == record1

        self._log_info("registration of threebot '{%s}' done" % name)

        return record1

    def _reservation_create(self, expiration_provisioning, expiration_reservation):
        """
        Create a reservation object from schema url of "tfgrid.reservation.1".

        :param expiration_provisioning:
        :type expiration_provisioning: int
        :param expiration_reservation:
        :type expiration_reservation: int
        :return: reservation object
        :return type: obj
        """
        reservation_model = j.data.schema.get_from_url(url="tfgrid.reservation.1")

        reservation = reservation_model.new()
        reservation.customer_tid = j.tools.threebot.me.default.tid
        reservation.data_reservation.expiration_provisioning = int(j.data.time.epoch + 30 * 60)
        reservation.data_reservation.expiration_reservation = int(j.data.time.epoch + 50 * 60)

        return reservation

    def _container_add(
        self, reservation=None, node_id="", workload_id=1, flist="", hub_url="", environment={}, entrypoint=""
    ):
        """
        Create and add container workload to reservation.
        The parameters passed will be added to the container workload

        :param reservation: reservation object to add container to
        :type reservation: obj
        :param node_id: links to unique node on the TFGrid
        :type node_id: str
        :param workload_id: unique id inside the reservation is an autoincrement
        :type workload_id: int
        :param flist: link to flist to create a container from
        :type flist: str
        :param hub_url: link to hub
        :type hub_url: str
        :param environment: environment variables to be passed to the contiainer to be created eg : {"USER":"test_user"}
        :type environment: dict
        :param entrypoint: entrypoint to container start
        :type entrypoint: str
        :return: reservation object
        :return type: obj
        """
        if not reservation:
            raise j.exceptions.Value("You need to provide a reservation object")
        if not node_id:
            raise j.exceptions.Value("You need to provide a node_id value")
        # Create container workload
        container = reservation.data_reservation.containers.new()
        container.node_id = node_id
        container.workload_id = workload_id
        container.flist = flist
        container.hub_url = hub_url
        container.environment = environment or {}
        container.entrypoint = entrypoint or ""
        container.interactive = True  # yes or no

        return reservation

    def _network_add(
        self,
        reservation=None,
        node_id="",
        workload_id=2,
        wireguard_private_key_encrypted="",
        wireguard_public_key="",
        wireguard_listen_port=51820,
    ):
        if not reservation:
            raise j.exceptions.Value("You need to provide a reservation object")
        if not node_id:
            raise j.exceptions.Value("You need to provide a node_id value")
        # Create network workload
        # TODO create network for reservation
        # network = reservation.data_reservation.networks.new()
        # network.workload_id = node_id

        # stats_aggregator = network.stats_aggregator.new()
        # stats_aggregator.addr = ""
        # stats_aggregator.port = 123
        # stats_aggregator.secret = ""
        # network.stats_aggregator.append(stats_aggregator)

        # network_resource = network.network_resources.new()
        # network_resource.node_id = "2"
        # # hex encoded encrypted with public key of the node, generated by the tfgrid customer
        # network_resource.wireguard_private_key_encrypted = ""
        # network_resource.wireguard_public_key = ""
        # network_resource.wireguard_listen_port = 123
        # network_resource.iprange = "10.10.10.0/24"
        # peer = network_resource.peers.new()
        # peer.public_key = ""
        # peer.allowed_iprange = ""  #  (Liprange)# is the the same as iprange in the net_resource
        # peer.endpoint = ""  # optional, only needed to connect out
        # peer.iprange = "10.10.11.0/24"
        # network_resource.peers.append(peer)
        # network.network_resources.append(network_resource)

        # return reservation

    def container_create(
        self,
        container_node_id=0,
        volume_node_id=0,
        flist="",
        hub_url="",
        environment={},
        entrypoint="",
        expiration_provisioning=None,
        expiration_reservation=None,
    ):
        """
        Create and register a reservation using explorer workloads actor to deploy a container on a node

        :param container_node_id: links to unique node on the TFGrid to create container on
        :type container_node_id: str
        :param volume_node_id: links to unique node on the TFGrid with network on
        :type volume_node_id: str
        :param flist: link to flist to create a container from
        :type flist: str
        :param hub_url: link to hub
        :type hub_url: str
        :param environment: environment variables to be passed to the contiainer to be created eg : {"USER":"test_user"}
        :type environment: dict
        :param entrypoint: entrypoint to container start
        :type entrypoint: str
        :return: reservation object
        :return type: obj
        """
        if not container_node_id or not volume_node_id:
            raise j.exceptions.Value("You need to provide a container_node_id and volume_node_id values ")
        if not expiration_provisioning:
            expiration_provisioning = int(j.data.time.epoch + 30 * 60)
        if not expiration_reservation:
            expiration_reservation = int(j.data.time.epoch + 50 * 60)

        # Create container reservation
        reservation = self._reservation_create(
            expiration_provisioning=expiration_provisioning, expiration_reservation=expiration_provisioning
        )
        # Add container configurations
        self._container_add(
            reservation=reservation,
            node_id=container_node_id,
            workload_id=1,  # value is 1 as only one container is added in this scenario
            flist=flist,
            hub_url=hub_url,
            environment=environment,
            entrypoint=entrypoint,
        )
        # Add network configurations TODO
        # self._network_add(reservation=reservation, node_id=volume_node_id, workload_id=2)

        # Create reservation.json
        reservation.json = j.data.serializers.json.dumps(reservation.data_reservation._ddict)
        reservation_data = reservation._ddict

        # Sign reservation
        signature = j.tools.threebot.me.default.sign_bytes(reservation.json.encode())

        # Register reservation and sign
        reservation = self.actors.workload_manager.reservation_register(reservation_data)
        self.actors.workload_manager.sign_customer(reservation.id, binascii.hexlify(signature.signature))

        return reservation
