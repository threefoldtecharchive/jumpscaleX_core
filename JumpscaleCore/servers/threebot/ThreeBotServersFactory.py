from .ThreebotServer import ThreeBotServer
from Jumpscale import j
from .OpenPublish import OpenPublish


class ThreeBotServersFactory(j.baseclasses.object_config_collection_testtools):
    """
    Factory for 3bots
    """

    __jslocation__ = "j.servers.threebot"
    _CHILDCLASS = ThreeBotServer

    def _init(self, **kwargs):
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
        self._log_info("install done for threebot server.")

    def bcdb_get(self, name, secret="", use_zdb=False):
        return self.default.bcdb_get(name, secret, use_zdb)

    def local_start_default(self, web=False):
        """

        tbot_client = j.servers.threebot.local_start_default()

        will check if there is already one running, will create client to localhost & return
        gedis client
        :return:
        """
        if j.sal.nettools.tcpPortConnectionTest("localhost", 8901) == False:
            # means needs to be started
            self.install()
            self.default.stop()
            self.default.start(background=True, web=web)

        self.client = j.clients.gedis.get(name="threebot", port=8901)
        assert self.client.ping()

        return self.client

    def test(self, name="basic", wiki=False, web=False, fileserver=False):
        """

        kosmos 'j.servers.threebot.test(name="basic")'
        kosmos 'j.servers.threebot.test(name="onlystart")'
        :return:
        """

        self.local_start_default()

        self.client.actors.package_manager.package_add(
            "threebot_phonebook",
            git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/phonebook",
        )

        self.client.actors.package_manager.package_add(
            "tfgrid_directory",
            git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/tfgrid_directory",
        )

        self.client.actors.package_manager.package_add(
            "tfgrid_workloads",
            git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/tfgrid_workloads",
        )

        if fileserver:
            self.client.actors.package_manager.package_add(
                "threebot_fileserver",
                git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/fileserver",
            )

        if wiki:
            self.client.actors.package_manager.package_add(
                "tf_wiki",
                git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/wiki",
            )

        self.client.reload()

        if not name == "onlystart":

            self._test_run(name=name)
