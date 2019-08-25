from Jumpscale import j

from .OVHClient import OVHClient

JSConfigBaseFactory = j.baseclasses.object_config_collection


class OVHFactory(JSConfigBaseFactory):
    """
    """

    __jslocation__ = "j.clients.ovh"
    _CHILDCLASS = OVHClient

    def _init(self, **kwargs):
        self.__imports__ = "ovh"

    def get_manual(
        self,
        instance,
        appkey,
        appsecret,
        consumerkey="",
        endpoint="soyoustart-eu",
        ipxeBase="https://bootstrap.grid.tf/ipxe/master",
    ):
        """

        @PARAM instance is the name of this client

        Visit https://eu.api.soyoustart.com/createToken/

        IMPORTANT:
        for rights add get,post,put & delete rights
        for each of them put /*
        this will make sure you have all rights on all methods recursive

        to get your credentials

        endpoints:
            ovh-eu for OVH Europe API
            ovh-ca for OVH North-America API
            soyoustart-eu for So you Start Europe API
            soyoustart-ca for So you Start North America API
            kimsufi-eu for Kimsufi Europe API
            kimsufi-ca for Kimsufi North America API
            runabove-ca for RunAbove API

        """

        return self.get(
            instance=instance,
            appkey_=appkey,
            appsecret_=appsecret,
            consumerkey_=consumerkey,
            endpoint=endpoint,
            ipxeBase=ipxeBase,
        )

    # def node_get(self,instance=""):
    #     cl=j.clients.ovh.client_get(instance=instance)
    #     cl.serverInstall(name="", installationTemplate="ubuntu1704-server_64", sshKeyName="ovh",
    # useDistribKernel=True, noRaid=True, hostname="", wait=True)

    def test(self, appkey="", appsecret="", consumerkey=""):
        """
        do:
        kosmos 'j.clients.ovh.test("appkey", "appsecret", "consumerkey")'
        """
        client = self.get(
            instance="test",
            appkey_=appkey,
            appsecret_=appsecret,
            consumerkey_=consumerkey,
            endpoint="soyoustart-eu",
            ipxeBase="https://bootstrap.grid.tf/ipxe/development",
        )
        client._connect()
        self._log_debug(client.servers_list())
