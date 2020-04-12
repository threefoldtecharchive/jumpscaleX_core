import nacl

from Jumpscale import j
import binascii

JSConfigBase = j.baseclasses.object_config
# from nacl.signing import VerifyKey
# from nacl.public import PrivateKey, PublicKey, SealedBox
from Jumpscale.clients.gedis.GedisClient import GedisClientActors


class ThreebotClient(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.threebot.client
    name** = ""                     #is the bot dns
    tid** =  0 (I)                  #threebot id
    host = "127.0.0.1" (S)          #for caching purposes
    port = 8901 (ipport)            #for caching purposes
    pubkey = ""                     #for caching purposes
    """

    def _init(self, **kwargs):
        self._pubkey_obj = None
        self._verifykey_obj = None
        self._sealedbox_ = None
        self._gedis_connections = {}
        assert self.name != ""

    @property
    def actors_base(self):
        cl = j.clients.gedis.get(name=self.name, host=self.host, port=self.port, package_name="zerobot.base")
        return cl.actors

    def client_get(self, packagename):
        if not packagename in self._gedis_connections:
            key = "%s__%s" % (self.name, packagename.replace(".", "__"))
            cl = j.clients.gedis.get(name=key, port=8901, package_name=packagename)
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
                name="packagemanager", host=self.host, port=self.port, package_name="zerobot.admin"
            ).actors.package_manager
            for package in package_manager_actor.packages_list(status=status).packages:
                name = package.name
                if name not in self._gedis_connections:
                    g = j.clients.gedis.get(
                        name=f"{name}_{self.name}", host=self.host, port=self.port, package_name=name
                    )
                    self._gedis_connections[name] = g
                for k, v in self._gedis_connections[name].actors._ddict.items():
                    setattr(actors, k, v)
            return actors
        else:
            if package_name not in self._gedis_connections:
                g = j.clients.gedis.get(
                    name=f"{package_name}_{self.name}", host=self.host, port=self.port, package_name=package_name
                )
                self._gedis_connections[package_name] = g
            return self._gedis_connections[package_name].actors

    def reload(self):
        for key, g in self._gedis_connections.items():
            g.reload()

    @property
    def actors_all(self):
        return self.actors_get(status="installed")

    def encrypt_for_threebot(self, data, hex=False):
        """
        Encrypt data using the public key of the remote threebot
        :param data: data to be encrypted, should be of type binary

        @return: encrypted data hex or binary

        """
        if isinstance(data, str):
            data = data.encode()
        res = self._sealedbox.encrypt(data)
        if hex:
            res = binascii.hexlify(res)
        return res

    def verify_from_threebot(self, data, signature, data_is_hex=False):
        """
        :param data, if string will unhexlify else binary data to verify against verification key of the threebot who send us the data

        :return:
        """
        if isinstance(data, str) or data_is_hex:
            data = binascii.unhexlify(data)
        if len(signature) == 128:
            signature = binascii.unhexlify(signature)
        return self.verifykey_obj.verify(data, signature=signature)

    @property
    def _sealedbox(self):
        if not self._sealedbox_:
            self._sealedbox_ = SealedBox(self.pubkey_obj)
        return self._sealedbox_

    @property
    def pubkey_obj(self):
        if not self._pubkey_obj:
            self._pubkey_obj = self.verifykey_obj.to_curve25519_public_key()
        return self._pubkey_obj

    @property
    def verifykey_obj(self):
        if not self._verifykey_obj:
            assert self.pubkey
            verifykey = binascii.unhexlify(self.pubkey)
            assert len(verifykey) == 32
            self._verifykey_obj = VerifyKey(verifykey)
        return self._verifykey_obj

    def test_auth(self, bot_id):
        encryptor = j.me.encryptor
        encryptor._load_singing_key()
        epoch = str(j.data.time.epoch)
        signed_message = encryptor.sign(epoch.encode()).hex()
        cmd = "auth {} {} {}".format(bot_id, epoch, signed_message)
        return self._gedis._redis.execute_command(cmd)
