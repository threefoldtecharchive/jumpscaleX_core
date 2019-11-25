from Jumpscale import j

JSConfigClient = j.baseclasses.object_config


class TCPRouterClient(JSConfigClient):

    _SCHEMATEXT = """
        @url =  jumpscale.tcp_router.client.1
        name** = "" (S)
        local_address = "" (S)
        remote_address = "" (S)
        secret = "" (S)
        """

    def _init(self, **kwargs):
        self.trc_server = j.servers.startupcmd.get("trclient")

    def connect(self):
        """
        connect to tcprouter backend
        """
        cmd = f"trc -local {self.local_address} -remote {self.remote_address} -secret {self.secret}"
        self.trc_server.cmd_start = cmd
        if not self.trc_server.is_running():
            self.trc_server.start()

    def stop(self):
        """
        stop connection to tcprouter backend
        """
        self.trc_server.stop()
