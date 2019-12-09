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

    # def delete_ssh_key_from_ssh_directory(self):
    #     self.info("Check delete ssh key files from ssh directory using delete_from_sshdir method")
    #     self.sshkey_client.delete_from_sshdir()
    #     if not (
    #         os.path.isfile("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name))
    #         and os.path.isfile("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name))
    #     ):
    #         return True
    #     else:
    #         return False

    def test001_load_sshkey_client_into_database(self):
        """
        TC 469
        Test to load sshkey client into database.

        **Test scenario**
        #. Create sshkey client.
        #. Check the existence of the client in database, should be there.
        #. Delete sshkey client from database.
        #. Check the existence of the client in database, shouldn't be there.
        #. Load sshkey client into database.
        #. Check the existence of the client in database, should be there again.
        """
        self.info("Create sshkey client with name {}".format(self.sshkeyclient_name))
        self.info("Delete sshkey files from database".format(self.sshkey_client))
        self.assertTrue(
            self.delete_client_method(self.sshkey_client, "jumpscale.sshkey.client", self.sshkeyclient_name)
        )
        self.info("Load sshkey files from filesystem to database")
        self.sshkey_client.load_from_filesystem()
        self.info("Check the existence of the client in BCDB")
        model = j.data.bcdb.system.model_get(url="jumpscale.sshkey.client")
        self.assertTrue(model.get_by_name(name=self.sshkeyclient_name))

    def test02_generate_key(self):
        """
        TC 470
        Test generate ssh key.

        **Test scenario**
        #. Generate with reset=False option, should fail as it has been generated before in sshkey client.
        #. Use generate with reset=True option, this will regenerate the key.
        #. Make sure that keys have been regenerated.
        """
        self.info("Try generate method with option reset=False")
        with self.assertRaises(Exception) as error:
            self.sshkey_client.generate(reset=False)
            self.assertTrue("cannot generate key because pubkey already known" in error.exception.args[0])

        self.info("Use generate with reset=True option, this will regenerate the key")
        self.sshkey_client.generate(reset=True)
        self.info("Make sure that keys have been regenerated")
        self.assertTrue(os.path.isfile("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)))
        self.assertTrue(os.path.isfile("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)))
        old_privkey = self.ssh_privkey
        new_privkey = open("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)).read()
        old_pubkey = self.ssh_pubkey
        new_pubkey = open("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)).read()
        self.assertNotEqual(old_pubkey, new_pubkey)
        self.assertNotEqual(old_privkey, new_privkey)

    def test003_delete_ssh_key_from_ssh_directory(self):
        """
        TC 473
        Test delete sshkey files locally from ssh directory.

        **Test scenario**
        #. Use delete_from_sshdir to delete the sshkey files from ssh directory.
        #. Check the existence of those files in the sshkey directory.
        """
        self.info("Use delete_from_sshdir to delete the sshkey client files from ssh directory")
        self.assertTrue(self.delete_from_sshdir())

    def test004_write_sshkey_files_from_database_to_ssh_directory(self):
        """
        TC 474
        Test write sshkey files from database to ssh directory.

        **Test scenario**
        #. Delete sshkey files from ssh directory.
        #. Use write_to_sshdir method to write sshkey again to the directory from database.
        #. Check the existence of sshkey files in ssh directory, should be found
        #. Check the public and private keys values, should be the same as before.
        """
        self.info("Delete sshkey files from ssh directory")
        self.delete_from_sshdir()
        self.info("Use write_to_sshdir method to write sshkey again to the directory from database")
        self.sshkey_client.write_to_sshdir()
        self.info("Check the existence of sshkey files in ssh directory")
        self.assertTrue(os.path.isfile("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)))
        self.assertTrue(os.path.isfile("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)))
        self.info("Check the public and private keys values, should be the same as before")
        self.assertEqual(self.ssh_pubkey, open("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)).read())
        self.assertEqual(self.ssh_privkey, open("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)).read())

    def test005_load_sshkey_in_sshagent(self):
        """
        TC 475
        Test to load method which loads sshkey in sshagent.

        **Test scenario**
        #. Load sshkey in sshagent.
        #. Check if the ssh key has been loaded.
        """
        self.info("Load sshkey in sshagent")
        self.sshkey_client.load()
        self.info("Check if the ssh key has been loaded")
        output, error = self.os_command("ssh-add -l")
        self.assertIn("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name), output.decode())
        self.assertFalse(error)

    def test006_unload_sshkey_from_sshagent(self):
        """
        TC 476
        Test to unload method in sshkey client which unloads sshkey from sshagent.

        **Test scenario**
        #. Unload the sshkey from sshagent.
        #. Check that sshkey has been unloaded.
        """
        self.info("Unload the sshkey using the unload method")
        self.sshkey_client.unload()
        self.info("Check that sshkey has been unloaded")
        self.assertFalse(self.sshkey_client.is_loaded())
        output, error = self.os_command("ssh-add -l")
        self.assertNotIn(self.sshkeyclient_name, output.decode())

    def test007_key_is_loaded(self):
        """
        TC 477
        Test to key is loaded method in sshkey client, which checks if sshkey is loaded.

        **Test scenario**
        #. Load the sshkey in the sshagent.
        #. Check if the key has been loaded.
        #. Remove the sshkey from sshagent.
        #. Check if the key has been unloaded.
        """
        self.info("Load the sshkey in the sshagent")
        self.sshkey_client.load()
        self.info("Check if the key has been loaded")
        self.assertTrue(self.sshkey_client.is_loaded())
        self.info("Remove the sshkey from sshagent")
        self.sshkey_client.unload()
        self.info("Check if the key has been unloaded")
        self.assertFalse(self.sshkey_client.is_loaded())

    def test008_get_public_key(self):
        """
        TC 478
        Test to get public key in sshkey client.

        **Test scenario**
        #. Create sshkey client, and get the public key (pk1)
        #. Check the public key for sshkey client (pk2) using pubkey_only method, should be the same as pk1.
        """
        self.info("Check the public key for sshkey client")
        ssh_key_pubkey_only = self.sshkey_client.pubkey_only
        pubkey_only = open("/{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)).read().split()[1]
        self.assertEqual(ssh_key_pubkey_only, pubkey_only)
