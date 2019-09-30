import os.path
from Jumpscale import j
from .base_test import BaseTest


class TestSshkeyClient(BaseTest):

    @classmethod
    def setUpClass(cls):
        BaseTest.info("create sshkey client")
        cls.sshkey_client = j.clients.sshkey.get(name="sshkey_client")

    def setUp(self):
        print('\t')
        self.info('Test case : {}'.format(self._testMethodName))

    def test001_pubkey(self):
        """
        TC
        Test case for public key method on sshkey client

        **Test scenario**
        #. compare the output from this method with the contact of /root/.ssh/sshkey_client.pub

        """
        self.info("check pubkey method in sshkey client")
        ssh_key_pubkey = self.sshkey_client.pubkey
        self.assertEqual(ssh_key_pubkey, open('/root/.ssh/sshkey_client.pub').read())
        return ssh_key_pubkey

    def test002_privkey(self):
        """
        TC
        Test case for private key method on sshkey client

        **Test scenario**
        #. compare the output from this method with the contact of /root/.ssh/sshkey_client
        """
        self.info("check privkey method in sshkey client")
        ssh_key_privkey = self.sshkey_client.privkey
        self.assertEqual(ssh_key_privkey, open('/root/.ssh/sshkey_client').read())
        return ssh_key_privkey

    def test003_name(self):
        """
        TC
        Test case for name method of sshkey client

        **Test scenario**
        #. check the name of sshkey client it must equal to sshkey_client
        """
        self.info("check name method in sshkey client")
        ssh_key_name = self.sshkey_client.name
        self.assertEqual(ssh_key_name, "sshkey_client")

    def test004_path(self):
        """
        TC
        Test case for path of sshkey client

        **Test scenario**
        #. check the path of sshkey client it must equal to /root/.ssh/sshkey_client
        """
        self.info("check path method in sshkey client, it should equal to /root/.ssh/sshkey_client")
        ssh_key_path = self.sshkey_client.path
        self.assertEqual(ssh_key_path, '/root/.ssh/sshkey_client')

    def test005_pubkey_only(self):
        """
        TC
        Test case for pubkey_only method in sshkey client

        **Test scenario**
        #. check the pubkey_only for sshkey client
        """
        self.info("check pubkey_only method in sshkey client")
        ssh_key_pubkey_only = self.sshkey_client.pubkey_only
        pubkey_only = open('/root/.ssh/sshkey_client').read().split()[1]
        self.assertEqual(ssh_key_pubkey_only, pubkey_only)

    def test006_delete_from_sshdir(self):
        """
        TC
        Test case for delete_from_sshdir method in sshkey client

        **Test scenario**
        #. use delete_from_sshdir to delete the sshkey_client files from ssh directory
        #. check the existence of those files (sshkey_client & sshkey_client.pub) in the sshkey directory.
        """
        self.info("check delete_from_sshdir method in sshkey client")
        self.sshkey_client.delete_from_sshdir()
        self.info("check that sshkey_client files are deleted from ssh directory")
        self.assertFalse(os.path.isfile('/root/.ssh/sshkey_client'))
        self.assertFalse(os.path.isfile('/root/.ssh/sshkey_client.pub'))

    def test007_write_to_sshdir(self):
        """
        TC
        Test case for write_to_sshdir method in sshkey client

        **Test scenario**
        #. use write_to_sshdir method to write sshkey again to the directory.
        #. check the existence of those files (sshkey_client & sshkey_client.pub) in the sshkey directory.
        #. check the public and private keys should be the same as before
        """
        self.info("check write_to_sshdir method in sshkey client")
        self.sshkey_client.write_to_sshdir()
        self.info("check that sshkey_client files are in ssh directory, and with the old values")
        old_pubkey = self.test001_pubkey.ssh_key_pubkey
        self.assertEqual(old_pubkey, open('/root/.ssh/sshkey_client.pub').read())
        old_privkey = self.test002_privkey.ssh_key_privkey
        self.assertEqual(old_privkey, open('/root/.ssh/sshkey_client').read())

    def test008_generate(self):
        """
        TC
        Test case to test generate method with option reset=True in sshkey client

        **Test scenario**
        #. use generate method with option reset=True, this will regenerate the key.
        #. check the existence of the new key, and make sue that it's new one.
        """
        self.info("check generate method with option reset=True")
        self.sshkey_client.generate(reset=True)
        self.info("check that sshkey_client files are in ssh directory, and with the new values")
        self.assertFalse(os.path.isfile('/root/.ssh/sshkey_client'))
        self.assertFalse(os.path.isfile('/root/.ssh/sshkey_client.pub'))
        old_privkey = self.test002_privkey.ssh_key_privkey
        new_privkey = open('/root/.ssh/sshkey_client').read()
        old_pubkey = self.test001_pubkey.ssh_key_pubkey
        new_pubkey = open('/root/.ssh/sshkey_client.pub').read()
        self.assertNotEqual(old_pubkey, new_pubkey)
        self.assertNotEqual(old_privkey, new_privkey)

