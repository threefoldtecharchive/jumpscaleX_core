from unittest import TestCase, skip
from uuid import uuid4

from Jumpscale import j
from parameterized import parameterized
from loguru import logger

LOGGER = logger
LOGGER.add("PACKAGE_MANAGER_{time}.log")

PACKAGE_NAME = "test_package"


class TestPackageManager(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result_path = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), PACKAGE_NAME, "result")
        self.gedis_client = j.servers.threebot.start()
        self.package_manager = self.gedis_client.actors.package_manager
        self.path = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), PACKAGE_NAME)

    @staticmethod
    def random_string():
        return str(uuid4())[:10]

    @staticmethod
    def info(message):
        LOGGER.info(message)

    def get_package(self, package_name):
        packages = self.package_manager.packages_list().packages
        for package in packages:
            if package.name == package_name:
                return package
        return None

    def tearDown(self):
        self.package_manager.package_delete(PACKAGE_NAME)
        j.sal.fs.remove(self.result_path)
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        j.servers.threebot.default.stop()
        super().tearDownClass()

    @parameterized.expand(["path", "giturl"])
    def test_001_package_add(self, method):
        """
        Test case for adding package (test package) in threebot server

        **Test scenario**
        #. Start threebot server.
        #. Add test package.
        #. Check that the test package has been added.
        """
        self.info("Add test package.")
        if method == "path":
            package = {"path": self.path}
        else:
            giturl = "https://github.com/threefoldtech/jumpscaleX_core/tree/master/JumpscaleCore/servers/threebot/tests/test_package"
            package = {"git_url": giturl}

        self.package_manager.package_add(**package)
        self.gedis_client.reload()

        self.info("Check that the test package has been added.")
        content = j.sal.fs.readFile(self.result_path)
        self.assertIn("preparing package", content)
        self.assertIn("starting packag", content)

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/183")
    def test_002_package_list_delete(self):
        """
        Test case for listing and deleting packages

        **Test scenario**
        #. Start threebot server.
        #. Add test package.
        #. List packages, test package should be found.
        #. Delete test package.
        #. List packages again, test package should not be found.
        """
        self.info("Add test package.")
        self.package_manager.package_add(path=self.path)
        self.gedis_client.reload()

        self.info("List packages, test_package should be found.")
        package = self.get_package(PACKAGE_NAME)
        self.assertTrue(package, "Package not found after adding it")

        self.info("Delete test package.")
        self.package_manager.package_delete(PACKAGE_NAME)
        content = j.sal.fs.readFile(self.result_path)
        self.assertIn("uninstalling package", content)

        # TODO: check that there is no model in bcdb for this package

        self.info("List packages again, test_package should not be found.")
        package = self.get_package(PACKAGE_NAME)
        self.assertFalse(package, "Package found after deleting it")

    def test_003_package_enable_disable(self):
        """
        Test case for enabling and disabling packages.

        **Test scenario**
        #. Add test package.
        #. Enable this package.
        #. Check that package is enabled.
        #. Disable this package.
        #. Check that package
        """
        self.info("Add test package.")
        self.package_manager.package_add(path=self.path)
        self.gedis_client.reload()

        package = self.get_package(PACKAGE_NAME)
        self.assertTrue(package, "Package is not found after adding it")
        self.assertEqual(package.status, "RUNNING")

        self.info("Enable this package.")
        self.package_manager.package_enable(PACKAGE_NAME)

        self.info("Check that package is enabled.")
        package = self.get_package(PACKAGE_NAME)
        self.assertTrue(package, "Package is not found after adding it")
        self.assertEqual(package.status, "INSTALLED")

        self.info("Disable this package.")
        self.package_manager.package_disable(PACKAGE_NAME)

        self.info("Check that package")
        package = self.get_package(PACKAGE_NAME)
        self.assertTrue(package, "Package is not found after adding it")
        self.assertEqual(package.status, "DISABLED")

    def test_004_package_start_stop(self):
        """
        Test case for starting and stopping packages.

        **Test scenario**
        #. Add test package.
        #. Stop this package.
        #. Check that this package has been stopped.
        #. Start this package.
        #. Check that this package has been started.
        """
        self.info("Add test package.")
        self.package_manager.package_add(path=self.path)
        self.gedis_client.reload()

        package = self.get_package(PACKAGE_NAME)
        self.assertTrue(package, "Package is not found after adding it")
        self.assertEqual(package.status, "RUNNING")

        self.info("Stop this package.")
        self.package_manager.package_stop(PACKAGE_NAME)

        self.info("Check that this package has been stopped.")
        package = self.get_package(PACKAGE_NAME)
        self.assertTrue(package, "Package is not found after adding it")
        self.assertEqual(package.status, "HALTED")

        content = j.sal.fs.readFile(self.result_path)
        self.assertIn("stopping package", content)
        j.sal.fs.remove(self.result_path)

        self.info("Start this package.")
        self.package_manager.package_start(PACKAGE_NAME)

        self.info("Check that this package has been started.")
        package = self.get_package(PACKAGE_NAME)
        self.assertTrue(package, "Package is not found after adding it")
        self.assertEqual(package.status, "RUNNING")

        content = j.sal.fs.readFile(self.result_path)
        self.assertIn("starting package", content)
