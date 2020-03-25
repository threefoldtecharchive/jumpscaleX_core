from Jumpscale import j

from .ThreebotClient import ThreebotClient
from io import BytesIO

JSConfigBase = j.baseclasses.object_config_collection
skip = j.baseclasses.testtools._skip


class ThreebotClientFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.threebot"
    _CHILDCLASS = ThreebotClient

    def _init(self, **kwargs):
        self._id2client_cache = {}

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
            if threebot <= 0:
                raise j.exceptions.Input("threebot ID must be a positive integer")

            if threebot in self._id2client_cache:
                return self._id2client_cache[threebot]
            tid = threebot
            tname = None
        elif isinstance(threebot, str):
            tid = None
            tname = threebot
        else:
            raise j.exceptions.Input("threebot needs to be int or str")

        r = j.clients.explorer.default.users.get(tid=tid, name=tname)
        if r.id <= 0:
            raise j.exceptions.Input("threebot ID must be a positive integer")

        client = j.baseclasses.object_config_collection_testtools.get(
            self, name=r.name, tid=r.id, host=r.ipaddr, pubkey=r.pubkey
        )

        self._id2client_cache[client.tid] = client
        return self._id2client_cache[client.tid]

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/487")
    def test(self):
        """
        kosmos 'j.clients.threebot.test()'
        :return:
        """
        e = j.clients.threebot.explorer
        a = e.actors_base
        assert a.system.ping() == b"PONG"

        a2 = e.actors_get("threebot.blog")

        p = e.actors_get("zerobot.packagemanager")

        l = p.package_manager.packages_list()

        pnames = [p.name for p in p.package_manager.packages_list().packages]

        l = p.package_manager.actors_list()

        j.shell()
