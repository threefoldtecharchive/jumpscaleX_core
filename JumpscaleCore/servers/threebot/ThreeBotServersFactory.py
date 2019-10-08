from .ThreebotServer import ThreeBotServer
from Jumpscale import j

# from .OpenPublish import OpenPublish


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

    def install(self, force=True):
        def need_install():
            for cmd in ["resty", "lua", "sonic", "zdb"]:
                if not j.core.tools.cmd_installed(cmd):
                    return True
            return False

        fallback_ssl_key_path = "/sandbox/cfg/ss/resty-auto-ssl-fallback.crt"
        if force or need_install() or not j.sal.fs.exists(fallback_ssl_key_path):
            j.servers.openresty.install()
            j.builders.web.openresty.install()
            j.builders.runtimes.lua.install()
            j.builders.db.zdb.install()
            j.builders.apps.sonic.install()
            self._log_info("install done for threebot server.")

    def bcdb_get(self, name, secret="", use_zdb=False):
        return self.default.bcdb_get(name, secret, use_zdb)

    def local_start_default(self, web=True, packages_add=False):
        """

        kosmos -p 'j.servers.threebot.local_start_default()'

        tbot_client = j.servers.threebot.local_start_default()

        will check if there is already one running, will create client to localhost & return
        gedis client
        :return:
        """
        if j.sal.nettools.tcpPortConnectionTest("localhost", 8901) == False:
            self.install()
            self.default.stop()

        # will return client
        client = self.default.start(background=True, web=web)

        client.actors.package_manager.package_add(path=j.threebot.package.phonebook._dirpath)

        if packages_add:
            client.actors.package_manager.package_add(
                git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/development/ThreeBotPackages/threefold/phonebook"
            )

            # client.actors.package_manager.package_add(
            #     git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/development/ThreeBotPackages/threebot/fileserver"
            # )

            client.actors.package_manager.package_add(
                git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/development/ThreeBotPackages/threebot/wiki"
            )

            client.reload()

        return client

    def test(self, name="threebot_phonebook", wiki=True, web=False, fileserver=False):
        """

        kosmos 'j.servers.threebot.test(name="basic")'
        kosmos 'j.servers.threebot.test(name="onlystart")'
        :return:
        """

        gedis_client = j.servers.threebot.local_start_default(web=True)

        gedis_client.actors.package_manager.package_add(
            git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/phonebook"
        )

        # self.client.actors.package_manager.package_add(
        #     "tfgrid_directory",
        #     git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/tfgrid_directory",
        # )

        # self.client.actors.package_manager.package_add(
        #     "tfgrid_workloads",
        #     git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/tfgrid_workloads",
        # )

        if fileserver:
            gedis_client.actors.package_manager.package_add(
                git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threebot/fileserver"
            )

        if wiki:
            gedis_client.actors.package_manager.package_add(
                git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/development/ThreeBotPackages/threebot/wiki"
            )

        gedis_client.reload()

        if not name == "onlystart":

            self._test_run(name=name)

    def _docker_jumpscale_get(self, name="3bot", delete=True):
        docker = j.core.dockerfactory.container_get(name=name, delete=delete)
        docker.install()
        docker.jumpscale_install()
        # now we can access it over 172.0.0.2
        return docker

    def docker_environment(self, delete=True):
        """
        kosmos 'j.servers.threebot.docker_environment(delete=True)'
        kosmos 'j.servers.threebot.docker_environment(delete=False)'

        will create a main container with jummpscale & 3bot
        will start wireguard connection on OSX
        will start threebot

        :return:
        """
        docker = self._docker_jumpscale_get(name="3bot", delete=delete)
        if j.core.myenv.platform() != "linux":
            # only need to use wireguard if on osx or windows (windows not implemented)
            docker.sshexec("source /sandbox/env.sh;jsx wireguard")  # get the wireguard started
            docker.wireguard.connect()

        self._log_info("check we can reach the container")
        assert j.sal.nettools.waitConnectionTest(docker.config.ipaddr, 22, timeout=30)

        self._log_info("start the threebot server")
        docker.sshexec(
            "source /sandbox/env.sh;kosmos 'j.servers.threebot.local_start_default(web=True,packages_add=True)'"
        )
        j.shell()

    def docker_environment_multi(self):
        pass
