import nacl

from Jumpscale import j
import binascii

JSConfigBase = j.baseclasses.object_config
from nacl.signing import VerifyKey
from nacl.public import PrivateKey, PublicKey, SealedBox
from Jumpscale.clients.gedis.GedisClient import GedisClientActors


class ThreebotClient(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.threebot.client
    name** = ""                     #is the bot dns
    tid** =  0 (I)                  #threebot id
    host = "127.0.0.1" (S)          #for caching purposes
    port = 8901 (ipport)            #for caching purposes
    pubkey = "" public key hex encoded of the 3bot we connect to
    """

    def _init(self, **kwargs):
        self._gedis_connections = {}
        assert self.name != ""

    @property
    def actors_base(self):
        cl = j.clients.gedis.get(
            name=self.name, host=self.host, port=self.port, server_pk_hex=self.pubkey, package_name="zerobot.base"
        )
        return cl.actors

    def client_get(self, packagename):
        if not packagename in self._gedis_connections:
            key = "%s__%s" % (self.name, packagename.replace(".", "__"))
            cl = j.clients.gedis.get(
                name=key, host=self.host, port=self.port, server_pk_hex=self.pubkey, package_name=packagename
            )
            self._gedis_connections[packagename] = cl
        return self._gedis_connections[packagename]

    def actors_get(self, package_name=None, status="installed"):
        """Get actors for package_name given. If status="all" then all the actors will be returned

        :param package_name: name of package to be loaded that has the actors needed. If value is "all" then all actors from all packages are retrieved
        :type package_name: str
        :return: actors of package(s)
        :type return: GedisClientActors (contains all the actors as properties)
        """
        if not package_name:
            actors = GedisClientActors()

            package_manager_actor = j.clients.gedis.get(
                name="packagemanager",
                host=self.host,
                port=self.port,
                server_pk_hex=self.pubkey,
                package_name="zerobot.packagemanager",
            ).actors.package_manager

            for package in package_manager_actor.packages_list(status=status).packages:
                name = package.name
                if name not in self._gedis_connections:
                    g = j.clients.gedis.get(
                        name=f"{name}_{self.name}",
                        host=self.host,
                        port=self.port,
                        server_pk_hex=self.pubkey,
                        package_name=name,
                    )
                    self._gedis_connections[name] = g
                for k, v in self._gedis_connections[name].actors._ddict.items():
                    setattr(actors, k, v)
            return actors
        else:
            if package_name not in self._gedis_connections:
                g = j.clients.gedis.get(
                    name=f"{package_name}_{self.name}",
                    host=self.host,
                    port=self.port,
                    server_pk_hex=self.pubkey,
                    package_name=package_name,
                )
                self._gedis_connections[package_name] = g
            return self._gedis_connections[package_name].actors

    def reload(self):
        for key, g in self._gedis_connections.items():
            g.reload()

    @property
    def actors_all(self):
        return self.actors_get(status="installed")
