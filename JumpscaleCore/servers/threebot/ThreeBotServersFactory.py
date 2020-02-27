from .ThreebotServer import ThreeBotServer
from Jumpscale import j
import time

TESTTOOLS = j.baseclasses.testtools

# from .OpenPublish import OpenPublish

skip = j.baseclasses.testtools._skip


class ThreeBotServersFactory(j.baseclasses.object_config_collection_testtools, TESTTOOLS):
    """
    Factory for 3bots
    """

    __jslocation__ = "j.servers.threebot"
    _CHILDCLASS = ThreeBotServer

    def _init(self, **kwargs):
        self._default = None
        self.current = None
        self.client = None
        if j.application.appname != "threebotserver" and j.application.state != "RUNNING":
            j.application.start("threebotserver")

    def _threebot_starting(self, starting=True):
        print("MARK THREEBOT IS STARTING")

        j.threebot.active = True
        if j.core.db and starting:
            j.core.db.set("threebot.starting", ex=120, value="1")
        j.data.bcdb._master_set()
        j.servers.myjobs
        j.tools.executor.local

    def threebotserver_check(self):
        if j.core.db and j.core.db.get("threebot.starting"):
            self.threebotserver_require()
            return True
        res = j.sal.nettools.tcpPortConnectionTest("localhost", 6380, timeout=0.1)
        return res

    def threebotserver_require(self, timeout=120):
        """
        see if we can find a local threebotserver, wait till timeout

        j.servers.threebot.threebotserver_require()

        :param timeout:
        :return:
        """
        timeout2 = j.data.time.epoch + timeout
        while j.data.time.epoch < timeout2:
            res = j.sal.nettools.tcpPortConnectionTest("localhost", 6380, timeout=0.1)
            if res and j.core.db.get("threebot.starting") is None:
                j.data.bcdb._master_set(False)
                return
            timedone = timeout2 - j.data.time.epoch
            print(" - wait threebotserver to start: %s" % timedone)
            time.sleep(0.5)
        raise j.exceptions.Base("please start threebotserver, could not reach in '%s' seconds." % timeout)

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

        fallback_ssl_key_path = j.core.tools.text_replace("{DIR_BASE}/cfg/ss/resty-auto-ssl-fallback.crt")
        if force or need_install() or not j.sal.fs.exists(fallback_ssl_key_path):
            j.servers.openresty.install()
            j.builders.db.zdb.install()
            j.builders.apps.sonic.install()
            self._log_info("install done for threebot server.")

    def bcdb_get(self, name, secret="", use_zdb=False):
        return self.default.bcdb_get(name, secret, use_zdb)

    def start(self, background=False, packages=None, reload=False, with_shell=True):
        """
        kosmos -p 'j.servers.threebot.start(background=True)'
        kosmos -p 'j.servers.threebot.start(background=False,with_shell=False)'
        kosmos -p 'j.servers.threebot.start(background=False,with_shell=True)'

        if background:
            will check if there is already one running, will create client to localhost & return
            gedis client to system actor

        :param: packages, is a list of packages_paths
            the packages need to reside in this repo otherwise they will not be found,
            centralized registration will be added but is not there yet

        :return:
        """
        if not background:
            self._threebot_starting()

        packages = packages or []

        if background:
            if reload:
                self.default.stop()

            if j.sal.nettools.tcpPortConnectionTest("localhost", 8901) is False:
                self.install()
                client = self.default.start(background=True, packages=packages)
                assert "." in client.package_name
            else:
                client = j.clients.gedis.get(name="threebot", port=8901)
                if not "." in client.package_name:
                    j.shell()
                assert "." in client.package_name

            # NO LONGER NEEDED BECAUSE PART OF DEFAULT>START
            # gediscl = j.clients.gedis.get("pkggedis", package_name="zerobot.packagemanager")
            # for package_path in packages:
            #     gediscl.actors.package_manager.package_add(path=package_path)

            client.reload()
            return client

        else:
            self.install()
            self.default.start(background=False, packages=packages, with_shell=with_shell)

    def local_start_3bot(self, background=False, reload=False):
        """starts 3bot with webplatform package.
        kosmos -p 'j.servers.threebot.local_start_3bot()'
        """
        if not background:
            self._threebot_starting()
        packages = [f"{j.dirs.CODEDIR}/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot/webplatform"]
        return self.start(background=background, packages=packages, reload=reload)

    def reset(self, debug=True):
        """

        resets your full 3bot with all data, CAREFUL

        kosmos -p 'j.servers.threebot.reset()'

        """
        j.data.bcdb._master_set()
        C = """
        rm -rf {DIR_BASE}/cfg/bcdb_config
        rm -rf {DIR_BASE}/cfg/bcdb
        rm -rf {DIR_BASE}/cfg/schema_meta.msgpack
        rm -rf {DIR_BASE}/cfg/sonic_config_threebot.cfg
        rm -rf {DIR_BASE}/var
        """
        if debug:
            j.core.myenv.config["LOGGER_LEVEL"] = 10
            j.core.myenv.config_save()
        j.clients.rdb.reset()
        j.servers.tmux.server.kill_server()
        C = j.core.tools.text_replace(C)
        j.sal.process.execute(C)

    def local_start_explorer(self, background=False, reload=False, with_shell=True):
        """

        starts 3bot with phonebook, directory, workloads packages.

        kosmos -p 'j.servers.threebot.local_start_explorer(with_shell=True)'
        kosmos -p 'j.servers.threebot.local_start_explorer(with_shell=False)'
        kosmos -p 'j.servers.threebot.local_start_explorer(with_shell=False,background=True)'

        """
        if not background:
            self._threebot_starting()
        packages = [
            f"{j.dirs.CODEDIR}/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/phonebook",
            f"{j.dirs.CODEDIR}/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/directory",
            f"{j.dirs.CODEDIR}/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/workloads",
        ]
        return self.start(background=background, packages=packages, reload=reload, with_shell=with_shell)

    def test(self, name=None, restart=False):
        """

        kosmos -p 'j.servers.threebot.test()'
        :return:
        """

        packages = ["threebot.blog"]

        cl = j.servers.threebot.start(background=True, packages=packages)

        # if fileserver:
        #     gedis_client.actors.package_manager.package_add(
        #         git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threebot/fileserver"
        #     )
        #
        # if wiki:
        #     gedis_client.actors.package_manager.package_add(
        #         git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/development/ThreeBotPackages/threebot/wiki"
        #     )
        #
        # gedis_client.reload()

        self._tests_run(name=name)

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/574")
    def test_explorer(self):
        """

        kosmos -p 'j.servers.threebot.test_explorer()'
        :return:
        """

        j.servers.threebot.local_start_explorer(background=True)
        j.shell()

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
        docker.sshexec("source /sandbox/env.sh;kosmos 'j.servers.threebot.start(packages_add=True)'")
        j.shell()

    def docker_environment_multi(self):
        pass
