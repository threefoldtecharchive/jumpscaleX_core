import os.path
from Jumpscale import j
from base_test import BaseTest


class TestSshKeyClient(BaseTest):
    def setUp(self):
        self.sshkeyclient_name = "ssh_client_{}".format(self.rand_string())
        self.sshkey_dir = "{}/.ssh".format(j.core.myenv.config["DIR_HOME"])
        self.info("Create sshkey client with name {}".format(self.sshkeyclient_name))
        self.sshkey_client = j.clients.sshkey.get(name=self.sshkeyclient_name)
        self.ssh_pubkey = self.sshkey_client.pubkey
        self.ssh_privkey = self.sshkey_client.privkey

        print("\t")
        self.info("Test case : {}".format(self._testMethodName))

    def tearDown(self):
        self.delete_from_sshdir()
        self.delete_client_method(self.sshkey_client, "jumpscale.sshkey.client", self.sshkeyclient_name)

    def delete_from_sshdir(self):
        self.info("Check delete_from_sshdir method in sshkey client, which delete ssh key files from ssh directory")
        self.sshkey_client.delete_from_sshdir()
        self.info("Check that sshkey files are deleted from ssh directory")
        if not (
            os.path.isfile("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name))
            and os.path.isfile("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name))
        ):
            return True
        else:
            return False

    def test001_load_from_filesystem(self):
        """
        TC 469
        Test load_from_filesyatem method which load sshkey files (public and private) from filesystem to database bcdb.

        **Test scenario**
        #. Use delete first to delete the client from database and check for the existence of it (it should be removed).
        #. Use load_from_filesystem method to load sshkey files from filesystem to database.
        #. Check the existence of the client in BCDB.
        """
        self.info("use delete_client_method to delete {} client".format(self.sshkey_client))
        self.assertTrue(
            self.delete_client_method(self.sshkey_client, "jumpscale.sshkey.client", self.sshkeyclient_name)
        )
        self.info("Use load_from_filesystem method to load sshkey files from filesystem to database")
        self.sshkey_client.load_from_filesystem()
        self.info("Check the existence of the client in BCDB")
        model = j.data.bcdb.system.model_get(url="jumpscale.sshkey.client")
        self.assertTrue(model.get_by_name(name=self.sshkeyclient_name))

    def test02_generate_key(self):
        """
        TC 470
        Test generate method which regenerates the sshkey.

        **Test scenario**
        #. Try generate method with option reset=False, should fail as it's generated before in sshkey client generation
        #. Use generate method with option reset=True, this will regenerate the key.
        #. Check the existence of the new key, and make sure that keys are new ones.
        """
        self.info("Try generate method with option reset=True")
        with self.assertRaises(Exception) as error:
            self.sshkey_client.generate(reset=False)
            self.assertTrue("cannot generate key because pubkey already known" in error.exception.args[0])

        self.info("Use generate method with option reset=True, this will regenerate the key")
        self.sshkey_client.generate(reset=True)
        self.info("Check the existence of the new key, and make sure that keys are new ones")
        self.assertTrue(os.path.isfile("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)))
        self.assertTrue(os.path.isfile("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)))
        old_privkey = self.ssh_privkey
        new_privkey = open("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)).read()
        old_pubkey = self.ssh_pubkey
        new_pubkey = open("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)).read()
        self.assertNotEqual(old_pubkey, new_pubkey)
        self.assertNotEqual(old_privkey, new_privkey)

    def test004_delete_from_sshdir(self):
        """
        TC 473
        Test delete_from_sshdir method, which delete sshkey files locally from ssh directory.

        **Test scenario**
        #. Use delete_from_sshdir to delete the sshkey_client files from ssh directory.
        #. Check the existence of those public and private key files in the sshkey directory.
        """
        self.info("Use delete_from_sshdir to delete the sshkey_client files from ssh directory.")
        self.assertTrue(self.delete_from_sshdir())

    def test005_write_to_sshdir(self):
        """
        TC 474
        Test case for write_to_sshdir method in sshkey client

        **Test scenario**
        #. Use delete_from_sshdir function make sure that the files have been deleted.
        #. Use write_to_sshdir method to write sshkey again to the directory.
        #. Check the existence of sshkey files (public and private) in directory in the sshkey directory.
        #. Check the public and private keys values, should be the same as before.
        """
        self.info("Use delete_from_sshdir function make sure that the files have been deleted")
        self.delete_from_sshdir()
        self.info("Use write_to_sshdir method to write sshkey again to the directory")
        self.sshkey_client.write_to_sshdir()
        self.info("Check the existence of sshkey files (public and private) in directory in the sshkey directory")
        self.assertTrue(os.path.isfile("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)))
        self.assertTrue(os.path.isfile("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)))
        self.info("Check the public and private keys values, should be the same as before")
        self.assertEqual(self.ssh_pubkey, open("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)).read())
        self.assertEqual(self.ssh_privkey, open("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)).read())

    def test006_load(self):
        """
        TC 475
        Test load method which loads sshkey in sshagent.

        **Test scenario**
        #. Use load method to load the sshkey in sshagent.
        #. Check the key is loaded or not from the output of the command (ssh-add -l).
        """
        self.info("Use load method to load the sshkey in sshagent")
        self.sshkey_client.load()
        self.info("Check the key is loaded or not from the output of the command (ssh-add -l).")
        output, error = self.os_command("ssh-add -l")
        self.assertIn("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name), output.decode())
        self.assertFalse(error)

    def test007_unload(self):
        """
        TC 476
        Test unload method in sshkey client which unloads sshkey from sshagent.

        **Test scenario**
        #. Unload the sshkey using the unload method.
        #. Check that sshkey in unloaded.
        """
        self.info("Unload the sshkey using the unload method")
        self.sshkey_client.unload()
        self.info("Check that sshkey in unloaded")
        self.assertFalse(self.sshkey_client.is_loaded())
        output, error = self.os_command("ssh-add -l")
        self.assertNotIn(self.sshkeyclient_name, output.decode())

    def test008_is_loaded(self):
        """
        TC 477
        Test is_loaded method in sshkey client, which checks if the sshkey is loaded.

        **Test scenario**
        #. Load the key and check if it has been loaded using is_load method, output should be True.
        #. Remove the sshkey from sshagent using unload method, and check is loaded or not, output should be False.
        """
        self.info("Load the key and check if it has been loaded using is_load method, output should be True")
        self.sshkey_client.load()
        self.assertTrue(self.sshkey_client.is_loaded())
        self.info(
            "Remove the sshkey from sshagent using unload method, and check is loaded or not, output should be False"
        )
        self.sshkey_client.unload()
        self.assertFalse(self.sshkey_client.is_loaded())

    def test009_pubkey_only(self):
        """
        TC 478
        Test pubkey_only method in sshkey client.

        **Test scenario**
        #. Check the pubkey_only for sshkey client.
        """
        self.info("Check the pubkey_only for sshkey client")
        ssh_key_pubkey_only = self.sshkey_client.pubkey_only
        pubkey_only = open("/{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)).read().split()[1]
        self.assertEqual(ssh_key_pubkey_only, pubkey_only)
