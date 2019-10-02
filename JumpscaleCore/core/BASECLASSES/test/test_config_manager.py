from Jumpscale import j
from .base_tests import BaseTest
from unittest import skip


class TestIConfigManager(BaseTest):
    def setUp(self):
        print("\n")
        self.info("Test case: {}".format(self._testMethodName))
        # create clients to be used in most tests. Use tfchain because it has a complex structure
        j.clients.tfchain._cache.reset()
        self.client_one = j.clients.tfchain.get("unittests_one", network_type="TEST")
        self.client_one.wallets.new("unittest_one")
        self.client_two = j.clients.tfchain.get("unittests_two", network_type="TEST")
        self.client_two.wallets.new("unittest_two")

    def tearDown(self):
        self.info("Delete test clients")
        j.clients.tfchain.delete(self.client_one.name)
        j.clients.tfchain.delete(self.client_two.name)

    def test01_create_new_client(self):
        """
        ** create new tfchain client with certain schema, should succeed **

        #. Create new tfchain client.
        #. Check the shema and make sure that the use is created successfully.
        """
        assert j.clients.tfchain._model.get_by_name(self.client_one.name)

    def test02_modify_exists_client(self):
        """
        ** Test update client data, should succeed **

        #. Update client's name.
        #. Check the updated name, should succeed.
        #. Check that you can't retrieve it using old name
        #. Check that deleting using the old name doesn't affect the new instance
        """
        self.info("Update tfchain client name")
        client_name = "unittest_one_new"
        self.client_one.name = client_name
        self.client_one.save()

        j.clients.tfchain.delete("unittest_one")
        with self.assertRaises(j.exceptions.NotFound):
            j.clients.tfchain.unittest_one

        self.info("Get client with new name")
        assert j.clients.tfchain.unittest_one_new
        assert j.clients.tfchain._model.get_by_name(client_name)

    def test03_delete_existing_client_from_factory(self):
        """
        ** Test delete tfchain client for existing client, should succeed. **

        #. Delete "unittest_one" client using factory delete.
        #. Check that the client is deleted successfully.
        #. Validate that unittest_two was not affected by unittest_one's deletion
        #. Check that the chidlren wallets are deleted properly but creating a new wallet with the same name.

        """
        self.info("Delete client {}".format(self.client_one.name))
        j.clients.tfchain.delete(self.client_one.name)
        self.info("Check that the client doesn't exist")
        with self.assertRaises(j.exceptions.NotFound):
            j.clients.tfchain._model.get_by_name(self.client_one.name)

        self.info("Check that the other client was not affected")
        j.clients.tfchain._model.get_by_name(self.client_two.name)
        assert "unittest_two" in self.client_two.wallets._children_names_get()

        self.info("Create a new wallet with the deleted client's wallet's name")
        assert self.client_two.wallets.new("unittest_one")

    def test04_delete_existing_client_from_instance_delete(self):
        """
        ** Test delete tfchain client for existing client, should succeed. **

        #. Delete "unittest_one" client using instance delete.
        #. Check that the client is deleted successfully.
        #. Validate that unittest_two was not affected by unittest_one's deletion
        #. Check that the wallets are deleted properly but creating a new wallet with the same name.

        """
        self.info("Delete client {}".format(self.client_one.name))
        self.client_one.delete()
        self.info("Check that the client doesn't exist")
        with self.assertRaises(j.exceptions.NotFound):
            j.clients.tfchain._model.get_by_name(self.client_one.name)

        self.info("Check that the other client was not affected")
        assert j.clients.tfchain._model.get_by_name(self.client_two.name)
        assert "unittest_two" in self.client_two.wallets._children_names_get()

        self.info("Create a new wallet with the deleted client's wallet's name")
        assert self.client_two.wallets.new("unittest_one")

    def test05_check_wallet_exist_under_correct_parent(self):
        """
        ** Test that each wallet is available under the correct tfchain client**
        """

        assert self.client_one.wallets.exists("unittest_one")
        assert not self.client_one.wallets.exists("unittest_two")

        assert self.client_two.wallets.exists("unittest_two")
        assert not self.client_two.wallets.exists("unittest_one")

    def test06_delete_wallet_from_client_using_instance_delete(self):
        """
        ** Test delete wallet from tfchain client using wallet.delete()**

        #. Delete "unittest_one" wallet from tfclient "unittest_one" using instance delete.
        #. Check that wallet "unittest_two" child of the other client was not affected
        #. check that the wallets are deleted properly by creating a new wallet with the same name.

        """
        self.info("Delete wallet unittest_one")
        self.client_one.wallets.unittest_one.delete()
        self.info("Check that the wallet doesn't exist")
        assert "unittest_one" not in self.client_one.wallets._children_names_get()

        self.info("Check that the other client's wallet was not affected")
        assert "unittest_two" in self.client_two.wallets._children_names_get()

        self.info("Create a new wallet with the deleted wallet's name")
        assert self.client_one.wallets.new("unittest_one")

    def test07_delete_wallet_from_client_using_factory_delete(self):
        """
        ** Test delete wallet from tfchain client using wallets.delete(wallet name)**

        #. Delete "unittest_one" wallet from tfclient "unittest_one" using factory delete.
        #. Check that wallet "unittest_two" child of the other client was not affected
        #. check that the wallets are deleted properly by creating a new wallet with the same name.

        """
        self.info("Delete wallet unittest_one")
        self.client_one.wallets.delete("unittest_one")
        self.info("Check that the wallet doesn't exist")
        assert "unittest_one" not in self.client_one.wallets._children_names_get()

        self.info("Check that the other client's wallet was not affected")
        assert "unittest_two" in self.client_two.wallets._children_names_get()

        self.info("Create a new wallet with the deleted wallet's name")
        assert self.client_one.wallets.new("unittest_one")

    def test08_delete_existing_clients_from_factory(self):
        """
        ** Test delete tfchain client for all existing clients, should succeed. **

        #. Delete all clients using factory delete.
        #. Check that all clients are deleted.

        """
        self.info("Delete all clients")
        j.clients.tfchain.delete()
        self.info("Check that the client doesn't exist")
        with self.assertRaises(j.exceptions.NotFound):
            j.clients.tfchain._model.get_by_name(self.client_one.name)

        with self.assertRaises(j.exceptions.NotFound):
            j.clients.tfchain._model.get_by_name(self.client_two.name)

        assert j.clients.tfchain.find() == []