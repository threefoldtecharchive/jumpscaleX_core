from .ThreebotServer import ThreeBotServer
from Jumpscale import j
from .OpenPublish import OpenPublish


class ThreeBotServersFactory(j.baseclasses.objects_config_bcdb, j.application.JSFactoryTools):
    """
    Factory for 3bots
    """

    __jslocation__ = "j.servers.threebot"
    _CHILDCLASS = ThreeBotServer

    def _init(self):
        self._default = None
        self.current = None
        self.client = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get("default")
        return self._default

    def install(self):
        j.builders.web.openresty.install()
        j.builders.runtimes.lua.install()
        j.builders.db.zdb.install()
        j.builders.apps.sonic.install()

    def bcdb_get(self, name, secret="", use_zdb=False):
        return self.default.bcdb_get(name, secret, use_zdb)

    def test(self, name="basic", wiki=False):
        """

        kosmos 'j.servers.threebot.test(name="basic")'
        kosmos 'j.servers.threebot.test(name="onlystart",wiki=True)'
        :return:
        """
        if j.sal.nettools.tcpPortConnectionTest("localhost", 5354) == False:
            # means needs to be started
            self.install()
            self.default.stop()
            self.default.start(background=True)

        self.client = j.clients.gedis.get(name="threebot")
        # self.client = j.clients.gedis.get(name="threebot", host="134.209.90.92")

        assert self.client.ping()

        self.client.actors.package_manager.package_add(
            "tf_directory",
            git_url="https://github.com/threefoldtech/digitalmeX/tree/development_jumpscale/threebot/packages/threefold/directory",
        )

        self.client.actors.package_manager.package_add(
            "threebot_phonebook",
            git_url="https://github.com/threefoldtech/digitalmeX/tree/development_jumpscale/threebot/packages/threefold/phonebook",
        )

        if wiki:
            self.client.actors.package_manager.package_add(
                "tf_wiki",
                git_url="https://github.com/threefoldtech/digitalmeX/tree/development_jumpscale/threebot/packages/threefold/wiki",
            )

        self.client.reload()

        if not name == "onlystart":

            self._test_run(name=name)
