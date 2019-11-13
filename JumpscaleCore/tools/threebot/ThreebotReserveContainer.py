import nacl, binascii

from Jumpscale import j


class ThreebotMe(j.baseclasses.object):
    """
    Create a reservation to deploy a container
    """

    __jslocation__ = "j.tools.threebot_reserve_container"

    def _init(self, **kwargs):
        # Get explorer threebot client instance
        self.explorer_tbot = j.clients.threebot.get("explorer_testnet", host="explorer.testnet.grid.tf", port="8901")

        ## Load and get reservation model
        j.data.schema.add_from_path(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/tfgrid_workloads/models"
        )
        self.reservation_model = j.data.schema.get_from_url(url="tfgrid.reservation.1")

    def _create_reservation(self, flist="", hub_url="", environment={}, entrypoint=""):

        reservation = self.reservation_model.new()
        reservation.customer_tid = j.tools.threebot.me.default.tid

        container_model = j.data.schema.get_from_url(url="tfgrid.reservation.container.1")
        container = container_model.new()
        container.node_id = "1"
        container.workload_id = 2
        container.flist = flist
        container.hub_url = hub_url
        container.environment = environment or {}
        container.entrypoint = entrypoint or ""
        container.interactive = "yes"  # yes or no
        reservation.data_reservation.containers.append(container)

        return reservation

    def create_container(self, flist, hub_url, environment, entrypoint):
        # Create container reservation
        reservation = self._create_reservation(flist, hub_url, environment, entrypoint)

        # Create reservation.json
        reservation.json = j.data.serializers.json.dumps(reservation.data_reservation._ddict)
        reservation_data = reservation._ddict

        # Sign reservation
        signature = j.tools.threebot.me.default.sign(reservation.json.encode())
        self.explorer_tbot.actors_get().workload_manager.sign_customer(
            reservation.id, binascii.hexlify(signature.signature)
        )

        # Register reservation
        reservation = self.explorer_tbot.actors_get().workload_manager.reservation_register(reservation_data)

        return reservation
