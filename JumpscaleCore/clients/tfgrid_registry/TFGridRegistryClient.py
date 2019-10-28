from Jumpscale import j


class TFGridRegistryClient(j.baseclasses.object):
    __jslocation__ = "j.clients.tfgrid_registry"

    def register(self, threebotclient, object, encrypted=False, authors=[], readers=[]):
        """

        client comes from j.clients.threebot.client_get(threebot="kristof.ibiza")

        register in easy way an object with our without schema
        :return:
        """
        pass

    def find(self, threebotclient):
        pass
