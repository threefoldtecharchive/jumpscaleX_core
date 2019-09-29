from Jumpscale import j

from .ThreebotClient import ThreebotClient
from io import BytesIO

JSConfigBase = j.baseclasses.object_config_collection


class ThreebotClientFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.threebot"
    _CHILDCLASS = ThreebotClient

    def _init(self, **kwargs):
        self._explorer = None
        self._cache = {}

    @property
    def explorer(self):
        if not self._explorer:
            self._explorer = j.baseclasses.object_config_collection_testtools.get(
                self, name="explorer", host="localhost"
            )
        return self._explorer

    @property
    def explorer_redis(self):
        cl = j.clients.redis.get(port=8901)
        cl.execute_command("config_format", "json")
        return cl

    def client_get(self, threebot=None):
        """

        returns a client connection to a threebot

        :param tid: threebot id
        :param name:
        :return:
        """
        # path to get a threebot client needs to be as fast as possible
        if id:
            assert threebot == None
            threebot = id
        if threebot in self._cache:
            return self._cache
        if isinstance(threebot, int):
            res = self.find(tid=threebot)
            tid = threebot
            tname = None
        elif isinstance(threebot, str):
            res = self.find(name=threebot)
            tid = None
            tname = threebot
        else:
            raise j.exceptions.Input("threebot needs to be int or str")

        if len(res) == 1:
            return res[0]
        elif len(res) > 1:
            raise j.exceptions.JSBUG("should never be more than 1")

        r = self.threebot_record_get(tid=tid, name=tname)
        r2 = j.baseclasses.object_config_collection_testtools.get(
            self, name=r.name, tid=r.tid, host=r.ipaddr, pubkey=r.pubkey
        )
        self._cache[threebot] = r2
        return self._cache[threebot]
