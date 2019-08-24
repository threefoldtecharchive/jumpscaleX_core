from Jumpscale import j
from .base_tests import BaseTest
from Jumpscale.core.InstallTools import BaseJSException


class TestIConfigManager(BaseTest):
    def setUp(self):
        print("\n")
        self.info("Test case: {}".format(self._testMethodName))

    def tearDown(self):
        self.info("Delete DataBase")
        j.data.bcdb.destroy_all()
        j.application.bcdb_system_destroy()

    def test01_create_new_client(self):
        """
        TC198

        ** create new user with certain schema, should success **
           we will use IYO client as an example 

        #. Create new github client, and save it.
        #. Check the shema and make sure that the use is created successfully. 
        """

        client_name = self.generate_random_str()
        self.info("Create github client {} and save it, should success".format(client_name))
        j.clients.github.new(client_name, token="test_create_new_client")
        self.info("Check that the client {} is created correctly".format(client_name))
        data = j.application.bcdb_system.get_all()
        self.assertEqual(client_name, data[-1].name)

    def test02_modify_exists_client(self):
        """
        TC195

        ** Test update user cleint data, should success ** 

        #. Update github "test_create_client" user token. 
        #. Check the updated token, should success. 
        """

        client_name = self.generate_random_str()
        self.info("Update github user token")
        c = j.clients.github.new(client_name, token="test_modify_client")
        c.token = "test_update"
        self.info("Save the changes")
        c.save()
        self.info("Check client token")
        data = j.application.bcdb_system.get_all()
        self.assertEqual("test_update", data[-1].token)

    def test03_delete_existing_client(self):
        """
        TC196

        ** Test delete github client for exists client, should success. **

        #. Delete "test_create_client" github client.
        #. check that the client is deleted successfully.

        """

        client_name = self.generate_random_str()
        self.info("Delete client {}".format(client_name))
        c = j.clients.github.new(client_name, token="test_delete_client")
        c.delete()
        self.info("Check that the client is not existing")
        with self.assertRaises(BaseJSException):
            j.clients.github.get(client_name)
