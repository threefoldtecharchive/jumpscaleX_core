import nacl

from Jumpscale import j

JSConfigBase = j.baseclasses.object_config


class ThreebotClient(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.threebot.client
    name* = ""                      #is the bot dns
    tid = 0 (I)                     #threebot id
    host = "127.0.0.1" (S)          #for caching purposes
    port = 8900 (ipport)            #for caching purposes
    pubkey = ""                     #for caching purposes
    namespace = "default" (S)
    """

    def _init(self, **kwargs):
        self._gedis = None
        assert self.name != ""

    @property
    def client(self):
        if not self._gedis:
            self._gedis = j.clients.gedis.get(name=self.name, host=self.host, port=self.port, namespace=self.namespace)
        return self._gedis

    def ping(self):
        return self.client.ping()

    # def auth(self, bot_id):
    #     nacl_cl = j.data.nacl.get()
    #     nacl_cl._load_privatekey()
    #     signing_key = nacl.signing.SigningKey(nacl_cl.privkey.encode())
    #     epoch = str(j.data.time.epoch)
    #     signed_message = signing_key.sign(epoch.encode())
    #     cmd = "auth {} {} {}".format(bot_id, epoch, signed_message)
    #     res = self._redis.execute_command(cmd)
    #     return res
