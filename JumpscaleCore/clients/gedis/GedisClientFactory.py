from Jumpscale import j

from .GedisClient import GedisClient

JSConfigBase = j.baseclasses.object_config_collection


class GedisClientCmds:
    def __init__(self, client):
        self._client = client
        self.__dict__.update(client.cmds.__dict__)

    def __str__(self):
        output = "Gedis Client: (instance=%s) (address=%s:%-4s)" % (
            self._client.name,
            self._client.host,
            self._client.port,
        )
        # if self._client.data.ssl:
        #     # FIXME: we should probably NOT print the key. this is VERY private information
        #     output += "\n(ssl=True, certificate:%s)" % self._client.sslkey
        return output

    __repr__ = __str__


class GedisClientFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.gedis"
    _CHILDCLASS = GedisClient

    def client_get(self, name="base", addr="localhost", port=8901, package_name="zerobot.base"):
        """

        :param addr:
        :param port:
        :param package_name: needs to be the full name which is $threebotauthor.$packagename
        :return:
        """

        return self.get(name=name, addr=addr, port=port, package_name=package_name)
