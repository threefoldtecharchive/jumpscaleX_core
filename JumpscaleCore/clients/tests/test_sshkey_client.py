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
        self.sshkey_client.delete_from_sshdir()
        self.delete_client_method(self.sshkey_client, "jumpscale.sshkey.client", self.sshkeyclient_name)

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
        self.info("Load sshkey client into database")
        self.sshkey_client.load_from_filesystem()
        self.info("Check the existence of the client in database")
        model = j.data.bcdb.system.model_get(url="jumpscale.sshkey.client")
        self.assertTrue(model.get_by_name(name=self.sshkeyclient_name))

    def test02_regenerate_sshkey(self):
        """
        TC 470
        Test to regenerate sshkey.

        **Test scenario**
        #. Create sshkey client, which generates public and private keys (pk1, priv_key1).
        #. Use generate method to regenerate the (public and private) keys, (pk2, priv_key2).
        #. Check that the keys have been regenerated, make sure that pk1 != pk2 and priv_key1 != priv_key2.
        """
        self.info("Use generate method to regenerate the (public and private) keys")
        self.sshkey_client.generate(reset=True)
        self.info("Check that the keys have been regenerated")
        self.assertTrue(os.path.isfile("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)))
        self.assertTrue(os.path.isfile("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)))
        old_privkey = self.ssh_privkey
        new_privkey = open("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)).read()
        old_pubkey = self.ssh_pubkey
        new_pubkey = open("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)).read()
        self.assertNotEqual(old_pubkey, new_pubkey)
        self.assertNotEqual(old_privkey, new_privkey)

    def test003_delete_sshkey_from_ssh_directory(self):
        """
        TC 473
        Test to delete sshkey files locally from ssh directory.

        **Test scenario**
        #. Create sshkey client.
        #. Use delete_from_sshdir to delete the sshkey client files from ssh directory.
        #. Check the existence of those files in the sshkey directory, shouldn't be there.
        """
        self.info("Use delete_from_sshdir to delete the sshkey client files from ssh directory")
        self.sshkey_client.delete_from_sshdir()
        self.info("Check the existence of those files in the sshkey directory, shouldn't be there")
        self.assertFalse(
            os.path.isfile("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name))
            and os.path.isfile("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name))
        )

    def test004_write_sshkey_files_into_ssh_directory(self):
        """
        TC 474
        Test to write sshkey files into ssh directory.

        **Test scenario**
        #. Create sshkey client.
        #. Check the existence of sshkey files (public [pk1] and private [priv_k1]) in ssh directory, should be there.
        #. Delete sshkey files from ssh directory.
        #. Use write_to_sshdir method to write sshkey again into the ssh directory.
        #. Check the existence of sshkey files in ssh directory, should be there.
        #. Check the public and private keys values, should be the same as (pk1, priv_k1).
        """
        self.info("Delete sshkey files from ssh directory")
        self.sshkey_client.delete_from_sshdir()
        self.info("Use write_to_sshdir method to write sshkey again into the ssh directory")
        self.sshkey_client.write_to_sshdir()
        self.info("Check the existence of sshkey files in ssh directory")
        self.assertTrue(os.path.isfile("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)))
        self.assertTrue(os.path.isfile("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)))
        self.info("Check the public and private keys values")
        self.assertEqual(self.ssh_pubkey, open("{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)).read())
        self.assertEqual(self.ssh_privkey, open("{}/{}".format(self.sshkey_dir, self.sshkeyclient_name)).read())

    def test005_load_sshkey_in_sshagent(self):
        """
        TC 475
        Test to load sshkey in sshagent.

        **Test scenario**
        #. Create sshkey client.
        #. Load sshkey in sshagent.
        #. Check that the sshkey has been loaded.
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
        Test to unload sshkey client from sshagent.

        **Test scenario**
        #. Create sshkey client.
        #. Unload the sshkey from sshagent.
        #. Check that the sshkey has been unloaded.
        """
        self.info("Unload the sshkey from sshagent")
        self.sshkey_client.unload()
        self.info("Check that sshkey has been unloaded")
        self.assertFalse(self.sshkey_client.is_loaded())
        output, error = self.os_command("ssh-add -l")
        self.assertNotIn(self.sshkeyclient_name, output.decode())

    def test007_sshkey_is_loaded(self):
        """
        TC 477
        Test to check if the sshkey is loaded in the sshagent.

        **Test scenario**
        #. Create sshkey client.
        #. Load the sshkey in the sshagent.
        #. Check that the key has been loaded.
        #. Remove the sshkey from sshagent.
        #. Check that the key has been unloaded.
        """
        self.info("Load the sshkey in the sshagent")
        self.sshkey_client.load()
        self.info("Check that the key has been loaded")
        self.assertTrue(self.sshkey_client.is_loaded())
        self.info("Remove the sshkey from sshagent")
        self.sshkey_client.unload()
        self.info("Check that the key has been unloaded")
        self.assertFalse(self.sshkey_client.is_loaded())

    def test008_get_public_key(self):
        """
        TC 478
        Test to get public key in sshkey client.

        **Test scenario**
        #. Create sshkey client, and get the public key (pk1).
        #. Check the public key for sshkey client (pk2) using pubkey_only method, should be the same as pk1.
        """
        self.info("Check the public key for sshkey client")
        ssh_key_pubkey_only = self.sshkey_client.pubkey_only
        pubkey_only = open("/{}/{}.pub".format(self.sshkey_dir, self.sshkeyclient_name)).read().split()[1]
        self.assertEqual(ssh_key_pubkey_only, pubkey_only)
