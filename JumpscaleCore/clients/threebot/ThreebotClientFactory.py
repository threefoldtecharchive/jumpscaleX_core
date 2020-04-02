from Jumpscale import j

from .ThreebotClient import ThreebotClient
from io import BytesIO

JSConfigBase = j.baseclasses.object_config_collection
skip = j.baseclasses.testtools._skip


class ThreebotClientFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.threebot"
    _CHILDCLASS = ThreebotClient

    def _init(self, **kwargs):
        # self._explorer = None
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
        explorer = j.clients.explorer.default

        record = None
        if isinstance(threebot, int):
            record = explorer.users.get(threebot)
        elif isinstance(threebot, str):
            users = explorer.users.list(name=threebot)
            if users:
                record = users[0]
        else:
            raise j.exceptions.Input("threebot needs to be int or str")

        if not record:
            j.exceptions.NotFound(f"threebot {threebot} not found")

        assert record.id > 0
        return j.baseclasses.object_config_collection_testtools.get(
            self, name=record.name, tid=record.id, host=record.ipaddr, pubkey=record.pubkey
        )

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
