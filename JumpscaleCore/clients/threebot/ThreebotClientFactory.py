from Jumpscale import j

from .ThreebotClient import ThreebotClient
from io import BytesIO

JSConfigBase = j.baseclasses.object_config_collection


class ThreebotClientFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.threebot"
    _CHILDCLASS = ThreebotClient

    def _init(self, **kwargs):
        self._explorer = None
        self._id2client_cache = {}

    @property
    def explorer_addr(self):
        if "EXPLORER_ADDR" not in j.core.myenv.config:
            return "localhost"
        else:
            return j.core.myenv.config["EXPLORER_ADDR"] + ""

    def explorer_addr_set(self, value):
        """

        :param value:
        :return:
        """
        j.core.myenv.config["EXPLORER_ADDR"] = value
        j.core.myenv.config_save()

    @property
    def explorer(self):
        if not self._explorer:
            self._explorer = j.baseclasses.object_config_collection_testtools.get(
                self, name="explorer", host=self.explorer_addr
            )
        return self._explorer

    @property
    def explorer_redis(self):
        cl = j.clients.redis.get(self.explorer_addr, port=8901)
        cl.execute_command("config_format", "json")
        return cl

    def client_get(self, threebot=None):
        """

        cl=j.clients.threebot.client_get(threebot="kristof.ibiza")
        cl=j.clients.threebot.client_get(threebot=10)

        returns a client connection to a threebot

        :param tid: threebot id
        :param name:
        :return:
        """
        # path to get a threebot client needs to be as fast as possible
        if isinstance(threebot, int):
            assert threebot > 0
            if threebot in self._id2client_cache:
                return self._id2client_cache[threebot]
            res = self.find(tid=threebot)
            tid = threebot
            tname = None
        elif isinstance(threebot, str):
            res = [self.get(name=threebot)]
            tid = None
            tname = threebot
        else:
            raise j.exceptions.Input("threebot needs to be int or str")

        if len(res) > 1:
            j.shell()
            raise j.exceptions.JSBUG("should never be more than 1")

        r = j.tools.threebot.explorer.threebot_record_get(tid=tid, name=tname)
        assert r.id > 0
        r2 = j.baseclasses.object_config_collection_testtools.get(
            self, name=r.name, tid=r.id, host=r.ipaddr, pubkey=r.pubkey
        )
        self._id2client_cache[r2.tid] = r2
        return self._id2client_cache[r2.tid]
