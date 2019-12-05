import unittest
from Jumpscale import j
from base_test import BaseTest


@unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/312")
class TestSshAgentClient(BaseTest):
    def setUp(self):
        self.SSHKEYCLIENT_NAME = "ssh_client_{}".format(self.rand_string())
        self.info("create sshkey client with name {}".format(self.SSHKEYCLIENT_NAME))

        self.PATH = "{}/.ssh/{}".format(j.core.myenv.config["DIR_HOME"], self.SSHKEYCLIENT_NAME)
        self.skey = j.clients.sshkey.get(name=self.SSHKEYCLIENT_NAME, path=self.PATH)
        self.skey.save()

        self.info("Start ssh-agent")
        self.os_command("eval `ssh-agent -s`")

        self.info("Set default sshkey agent name")
        j.clients.sshagent.key_default_name = self.SSHKEYCLIENT_NAME

        self.info("Set sshkey agent path")
        j.clients.sshagent.key_paths = self.PATH

        print("\t")
        self.info("Test case : {}".format(self._testMethodName))

    def tearDown(self):
        self.info("Delete sshkey files from ssh directory {}".format(self.SSHKEYCLIENT_NAME))
        self.skey.delete_from_sshdir()

        self.info("Delete sshkey client")
        self.skey.delete()

    def test001_start_and_kill_sshagent(self):
        """
        TC 570
        Test start and kill ssh agent.

        **Test scenario**
        #. Start ssh agent client.
        #. Load sshkey in sshagent.
        #. Check that ssh key is loaded.
        #. Try kill method in ssh agent client.
        #. Check that ssh key is unloaded.
        """
        self.info("Start ssh agent client")
        j.clients.sshagent.start()

        self.info("Load sshkey in sshagent")
        j.clients.sshagent.key_load()

        self.info("Check that ssh key is loaded")
        self.assertTrue(self.skey.is_loaded())

        self.info("Try kill method in ssh agent client")
        j.clients.sshagent.kill()

        self.info("Check that ssh key is unloaded")
        self.assertFalse(self.skey.is_loaded())

    def test002_keys_list_and_keypub_path_get(self):
        """
        TC 571
        Test list of ssh keys in sshagent, and public key path.

        **Test scenario**
        #. Load sshkey in sshagent.
        #. Check the list of the loaded ssh key in ssh agent using keys_list method in sshagent.
        #. Check the public key path of the loaded ssh key in ssh agent using keypub_path_get method in sshagent
        """
        self.info("Load sshkey in sshagent")
        j.clients.sshagent.key_load()

        self.info("Check the list of the loaded ssh key in ssh agent using keys_list method in sshagent")
        self.assertIn(self.PATH, j.clients.sshagent.keys_list())
        output, error = self.os_command("ssh-add -l")
        self.assertIn(self.PATH, output.decode())

        self.info(
            "Check the public key path of the loaded ssh key in ssh agent using keypub_path_get method in sshagent"
        )
        self.assertIn(self.PATH, str(j.clients.sshagent.keypub_path_get()))
