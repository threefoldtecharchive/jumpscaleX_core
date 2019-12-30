from time import sleep
from unittest import TestCase, skip

import requests
from loguru import logger
from Jumpscale import j

LOGGER = logger
LOGGER.add("Wikis_{time}.log")


class Wiki(TestCase):
    @staticmethod
    def info(message):
        LOGGER.info(message)

    def setUp(self):
        self.gedis = j.servers.threebot.local_start_default(background=True)

    @classmethod
    def tearDownClass(cls):
        j.sal.process.killall("tmux")

    def test001_check_threebot_ports(self):
        """
        Test case for checking threebot ports.

        **Test scenario**
        #. Check gedis port, should be found.
        #. Check zdb port, should be found.
        #. Check sonic port, should be found.
        """
        self.info("Check gedis port, should be found.")
        self.assertTrue(j.sal.nettools.tcpPortConnectionTest("localhost", 8901), "Gedis is not started.")

        self.info("Check zdb port, should be found.")
        self.assertTrue(j.sal.nettools.tcpPortConnectionTest("localhost", 9900), "zdb is not started.")

        self.info("Check sonic port, should be found.")
        self.assertTrue(j.sal.nettools.tcpPortConnectionTest("localhost", 1491), "sonic is not started.")

    def test002_check_gedis_is_started(self):
        """
        Test case for checking that gedis is started.

        **Test scenario**
        #. Ping gedis server, should return True.
        """
        self.info("Ping gedis server, should return True.")
        self.assertTrue(self.gedis.ping())

    def test003_check_zdb_is_started(self):
        """
        Test case for checking that zdb is started.

        **Test scenario**
        #. Check that zdb process is started.
        #. Get zdb client and check zdb is started using ping.
        """
        self.info("Check that zdb process is started.")
        self.assertTrue(j.sal.process.checkProcessRunning("zdb"))

        self.info("Get zdb client and check zdb is started using ping.")
        adminsecret_ = j.data.hash.md5_string(j.core.myenv.adminsecret)
        cl = j.clients.zdb.client_admin_get(name="test_wiki", port=9900, secret=adminsecret_)
        self.assertTrue(cl.ping())

    def test004_check_sonic_is_started(self):
        """
        Test case for checking that sonic is started.

        **Test scenario**
        #. Check that sonic process is started.
        """
        self.info("Check that sonic process is started.")
        self.assertTrue(j.sal.process.checkProcessRunning("sonic"))

    def test005_check_package_manager_actor_is_loaded(self):
        """
        Test case for checking that package manager actor is loaded.

        **Test scenario**
        #. Get gedis client for package manager.
        #. Check that package manager is one of gedis client's actors.
        """
        self.info("Get gedis client for package manager.")
        gedis_client = j.clients.gedis.get(
            name="test_wiki", host="127.0.0.1", port=8901, package_name="zerobot.packagemanager"
        )

        self.info("Check that package manager is one of gedis client's actors.")
        actors = gedis_client.actors
        self.assertIn("package_manager", dir(actors))

    @skip("https://github.com/threefoldtech/jumpscaleX_threebot/issues/321")
    def test006_check_web_interfaces(self):
        """
        Test case for checking web interfaces is loaded.
        """
        self.info("Running bottle web server test")
        j.tools.packages.webinterface.test()

    def test008_wiki_is_loaded(self):
        """
        Test case for checking wikis.

        **Test scenario**
        #. Load test wikis using package manager.
        #. Check the wikis is loaded, should be found.
        #. Remove the added test wiki.
        #. Check the added wiki, should not be found.
        """
        self.info("Load test wikis using markdowndocs.")
        gedis_client = j.clients.gedis.get(
            name="test_wiki", host="127.0.0.1", port=8901, package_name="zerobot.packagemanager"
        )
        wiki_path = j.core.tools.text_replace(
            "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot/wiki_examples"
        )
        gedis_client.actors.package_manager.package_add(path=wiki_path)
        sleep(60)

        self.info("Check the wikis is loaded, should be found.")
        r = requests.get("http://127.0.0.1/3git/wikis/zerobot.wiki_examples/test_include.md")
        self.assertEqual(r.status_code, 200)
        self.assertIn("includes 1", r.content.decode())

        self.info("Remove the added test wiki.")
        gedis_client.actors.package_manager.package_delete("zerobot.wiki_examples")
        j.sal.fs.remove("/docsites/zerobot.wiki_examples")

        self.info("Check the added wiki, should not be found.")
        r = requests.get("http://127.0.0.1/3git/wikis/zerobot.wiki_examples/test_include.md")
        self.assertEqual(r.status_code, 404)
