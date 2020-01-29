from Jumpscale import j
from base_test import BaseTest


class TestSshAgentClient(BaseTest):
    def setUp(self):
        self.SSHKEYCLIENT_NAME = "ssh_client_{}".format(self.rand_string())
        self.info("Create sshkey client with name {}".format(self.SSHKEYCLIENT_NAME))

        self.PATH = "{}/.ssh/{}".format(j.core.myenv.config["DIR_HOME"], self.SSHKEYCLIENT_NAME)
        self.sshkey_client = j.clients.sshkey.get(name=self.SSHKEYCLIENT_NAME, path=self.PATH)
        self.sshkey_client.save()

        self.info("Start ssh-agent")
        self.os_command("eval `ssh-agent -s`")

        self.info("Add sshkey to sshagent")
        self.os_command("ssh-add {}/.ssh/id_rsa".format(j.core.myenv.config["DIR_HOME"]))

        print("\t")
        self.info("Test case : {}".format(self._testMethodName))

    def tearDown(self):
        self.info("Delete sshkey files from ssh directory {}".format(self.SSHKEYCLIENT_NAME))
        self.sshkey_client.delete_from_sshdir()

        self.info("Delete sshkey client")
        self.sshkey_client.delete()

    def test001_start_and_kill_sshagent(self):
        """
        TC 570
        Test start and kill ssh agent.

        **Test scenario**
        #. Start ssh agent client.
        #. Load ssh keys in sshagent.
        #. Check that ssh key is loaded.
        #. Try kill method in ssh agent client.
        #. Check that ssh key is unloaded.
        """
        self.info("Start ssh agent client")
        j.clients.sshagent.start()

        self.info("Load sshkey in sshagent")
        j.clients.sshagent.key_load(path=self.PATH, name=self.SSHKEYCLIENT_NAME)

        self.info("Check that ssh key is loaded")
        self.assertTrue(self.sshkey_client.is_loaded())

        self.info("Try kill method in ssh agent client")
        j.clients.sshagent.kill()

        self.info("Check that ssh key is unloaded")
        self.assertFalse(self.sshkey_client.is_loaded())

    def test002_list_of_ssh_keys_in_sshagent(self):
        """
        TC 571
        Test to list of ssh keys in sshagent, and public key path.

        **Test scenario**
        #. Load sshkey in sshagent.
        #. Check if the ssh key is loaded using keys_list method.
        #. Check the public key path of the loaded ssh key using keypub_path_get method.
        """
        self.info("Load sshkey in sshagent")
        j.clients.sshagent.key_load(path=self.PATH, name=self.SSHKEYCLIENT_NAME)

        self.info("Check if the ssh key is loaded using keys_list method")
        self.assertIn(self.PATH, j.clients.sshagent.keys_list())
        output, error = self.os_command("ssh-add -l")
        self.assertIn(self.PATH, output.decode())
