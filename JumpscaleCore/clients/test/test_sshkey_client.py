import uuid
import os.path
from Jumpscale import j
from base_test import BaseTest


class TestSshKeyClient(BaseTest):

    def setUp(self):
        self.SSHKEYCLIENT_NAME = str(uuid.uuid4()).replace("-", "")[:10]
        self.info("create sshkey client with name {}".format(self.SSHKEYCLIENT_NAME))
        self.sshkey_client = j.clients.sshkey.get(name=self.SSHKEYCLIENT_NAME)
        self.ssh_pubkey = self.sshkey_client.pubkey
        self.ssh_privkey = self.sshkey_client.privkey

        print('\t')
        self.info('Test case : {}'.format(self._testMethodName))

    def tearDown(self):
        self.delete_from_sshdir()
        self.delete_client_method(self.sshkey_client, "jumpscale.sshkey.client", self.SSHKEYCLIENT_NAME)

    def delete_from_sshdir(self):
        self.info("check delete_from_sshdir method in sshkey client")
        self.sshkey_client.delete_from_sshdir()
        self.info("check that sshkey_client files are deleted from ssh directory")
        if not (os.path.isfile('/root/.ssh/{}.pub'.format(self.SSHKEYCLIENT_NAME))
                and os.path.isfile('/root/.ssh/{}'.format(self.SSHKEYCLIENT_NAME))):
            return True
        else:
            return False

    def test001_load_from_filesystem(self):
        """
        TC 469
        Test case for load_from_filesystem method in sshkey client

        **Test scenario**
        #. use delete first to delete the client from data base and check for the existence (it should be removed)
        #. use load_from_filesystem method to save it again to database
        #. check client existence
        """
        self.info("use delete_client_method to delete {} client".format(self.sshkey_client))
        self.assertTrue(self.delete_client_method(self.sshkey_client, "jumpscale.sshkey.client",
                                                  self.SSHKEYCLIENT_NAME))
        self.info("use load_from_filesystem to load sshkey")
        self.sshkey_client.load_from_filesystem()
        self.info("check the existence of the client in BCDB")
        model = j.data.bcdb.system.model_get(url="jumpscale.sshkey.client")
        self.assertTrue(model.get_by_name(name=self.SSHKEYCLIENT_NAME))

    def test02_generate_key_reset_False(self):
        """
        TC 470
        Test case for generate method with option (reset=False)

        **Test scenario**
        #. try to use generate method with option reset=False to regenerate the sshkey, should fail as it's generated
           before in sshkey client generation.
        """
        self.info("try generate method with option reset=True")
        with self.assertRaises(Exception):
            self.sshkey_client.generate(reset=False)

    def test003_generate_key_reset_True(self):
        """
        TC 471
        Test case to test generate method with option reset=True in sshkey client

        **Test scenario**
        #. use generate method with option reset=True, this will regenerate the key.
        #. check the existence of the new key, and make sue that it's new one.
        """
        self.info("check generate method with option reset=True")
        self.sshkey_client.generate(reset=True)
        self.info("check that sshkey_client files are in ssh directory, and with the new values")
        self.assertTrue(os.path.isfile('/root/.ssh/{}'.format(self.SSHKEYCLIENT_NAME)))
        self.assertTrue(os.path.isfile('/root/.ssh/{}.pub'.format(self.SSHKEYCLIENT_NAME)))
        old_privkey = self.ssh_privkey
        new_privkey = open('/root/.ssh/{}'.format(self.SSHKEYCLIENT_NAME)).read()
        old_pubkey = self.ssh_pubkey
        new_pubkey = open('/root/.ssh/{}'.format(self.SSHKEYCLIENT_NAME)).read()
        self.assertNotEqual(old_pubkey, new_pubkey)
        self.assertNotEqual(old_privkey, new_privkey)

    def test004_delete_from_sshdir(self):
        """
        TC 473
        Test case for delete_from_sshdir method in sshkey client

        **Test scenario**
        #. use delete_from_sshdir to delete the sshkey_client files from ssh directory.
        #. check the existence of those files public and private key files in the sshkey directory.
        """
        self.info("use delete_from_sshdir to delete the sshkey_client files from ssh directory.")
        self.assertTrue(self.delete_from_sshdir())

    def test005_write_to_sshdir(self):
        """
        TC 474
        Test case for write_to_sshdir method in sshkey client

        **Test scenario**
        #. use delete_from_sshdir function make sure that the files is deleted.
        #. use write_to_sshdir method to write sshkey again to the directory.
        #. check the existence of those files public and private files in directory in the sshkey directory.
        #. check the public and private keys values,  should be the same as before
        """
        self.info("use delete_from_sshdir to delete the ssh files from ssh directory")
        self.delete_from_sshdir()
        self.info("check write_to_sshdir method in sshkey client")
        self.sshkey_client.write_to_sshdir()
        self.info("check that sshkey_client public and private files are in ssh directory")
        self.assertTrue(os.path.isfile('/root/.ssh/{}.pub'.format(self.SSHKEYCLIENT_NAME)))
        self.assertTrue(os.path.isfile('/root/.ssh/{}'.format(self.SSHKEYCLIENT_NAME)))
        self.info("check the public and private keys values,  should be the same as before")
        self.assertEqual(self.ssh_pubkey, open('/root/.ssh/{}.pub'.format(self.SSHKEYCLIENT_NAME)).read())
        self.assertEqual(self.ssh_privkey, open('/root/.ssh/{}'.format(self.SSHKEYCLIENT_NAME)).read())

    def test006_load(self):
        """
        TC 475
        Test case for load method in sshkey client

        **Test scenario**
        #. use load method to to load the sshkey in sshkey agent.
        #. check the key is loaded or not from the output of the command (ssh-add -l)
        """
        self.info("check load method")
        self.sshkey_client.load()
        self.info("check the output of ssh-add -l")
        output, error = self.os_command("ssh-add -l")
        self.assertIn("/root/.ssh/{}".format(self.SSHKEYCLIENT_NAME), output.decode())
        self.assertFalse(error)

    def test007_unload(self):
        """
        TC 476
        Test case for unload method in sshkey client

        **Test scenario**
        #. unload the sshkey using the unload method.
        #. check the output of this method using is_loaded
        """
        self.info("use unload method to unload the sshkey")
        self.sshkey_client.unload()
        self.info("check is_loaded method in sshkey, output should be false")
        self.assertFalse(self.sshkey_client.is_loaded())

    def test008_is_loaded(self):
        """
        TC 477
        Test case for is_loaded method in sshkey client

        **Test scenario**
        #. load the key and check is it loaded or not using is_load method, output should be True.
        #. remove the sshkey from the agent using (ssh-add -d), and check is loaded or not, output should be False.
        """
        self.info("use load method to load the sshkey")
        self.sshkey_client.load()
        self.info("check is_loaded method in sshkey, output should be true")
        self.assertTrue(self.sshkey_client.is_loaded())
        self.info("check is_loaded method in sshkey after i unload the key, output should be false")
        self.sshkey_client.unload()
        self.assertFalse(self.sshkey_client.is_loaded())

    def test009_pubkey_only(self):
        """
        TC 478
        Test case for pubkey_only method in sshkey client

        **Test scenario**
        #. check the pubkey_only for sshkey client
        """
        self.info("check pubkey_only method in sshkey client")
        ssh_key_pubkey_only = self.sshkey_client.pubkey_only
        pubkey_only = open('/root/.ssh/{}.pub'.format(self.SSHKEYCLIENT_NAME)).read().split()[1]
        self.assertEqual(ssh_key_pubkey_only, pubkey_only)
