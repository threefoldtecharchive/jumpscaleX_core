from Jumpscale import j
from unittest import TestCase
from unittest import skip


class RegisteryTests(TestCase):

    bcdb = j.data.bcdb.get("threebot_registery")

    @classmethod
    def setUpClass(cls):
        cls.cl = cls.addRegistryPackage()

    @classmethod
    def addRegistryPackage(cls):
        # . Start threebot server, add registery package, then reload the client.
        cl = j.servers.threebot.local_start_default(web=True)
        cl.actors.package_manager.package_add(
            path=j.core.tools.text_replace("{DIR_BASE}/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/registry")
        )
        cl.reload()
        return cl

    def getNewUser(self):
        tid = j.data.idgenerator.generateRandomInt(1000, 9000)
        randStr = j.data.idgenerator.generateXCharID(10)
        return j.tools.threebot.me.get(randStr, tid=tid, email=randStr + "@test.com", tname=randStr + "_name")

    def getSchemaAndModel(self, country_code="02", description="test wiki about travel", topic="travel, food, it"):
        schema = """
            @url = threebot.registry.test.schema.1
            url = "" 
            description = ""
            topic = "{}" (E)
            tags = (LS)
        """.format(
            topic
        )
        randStr = j.data.idgenerator.generateXCharID(10)
        scm = j.data.schema.get_from_text(schema)
        model = self.bcdb.model_get(url=scm.url).new()
        model.url = randStr + ".com"
        model.tags = topic
        model.save()
        return schema, model

    def test001_RegisterationAndPrivacy(self):
        """RG001
        #. Start threebot server, add registery package, then reload the client.
        #. Register user1's data as public, should succeed
        #. Get user1's public data, should succeed
        #. Register user1's data as private with giving access to user2, should succeed
        #. Get data with user 2, should succeed
        #. Get data with unauthorized data, should not be able to get the data
        """

        schema, model = self.getSchemaAndModel()

        author = self.getNewUser()
        authorized_reader = self.getNewUser()
        unauthorized_reader = self.getNewUser()

        # . Register user1's data as public, should succeed
        data_id1 = j.clients.tfgrid_registry.register(
            schema=schema, authors=[author.tid], model=model, is_encrypted_data=False
        )
        self.assertTrue(data_id1, "Failed to register your content")

        # . Get user1's public data, should succeed
        data = j.clients.tfgrid_registry.get_data_by_id(data_id1, author.tid)
        self.assertEqual(model, data)

        # . Register user1's data as private with giving access to user2, should succeed
        data_id2 = j.clients.tfgrid_registry.register(
            schema=schema, authors=[author.tid], model=model, is_encrypted_data=True, readers=[authorized_reader.tid],
        )
        self.assertTrue(data_id2, "Failed to register your content")

        # . Get data with user 2, should succeed
        data = j.clients.tfgrid_registry.find_encrypted(authorized_reader.tid)
        self.assertEqual(model, data[-1])

        # . Get data with unauthorized data, should not be able to get the data
        data = j.clients.tfgrid_registry.find_encrypted(unauthorized_reader.tid)
        self.assertFalse(data)

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/221")
    def test002_CheckOnDataFormat(self):
        """RG002
        #. Start threebot server, add registery package, then reload the client.
        #. Register user1's data, should succeed
        #. Check if you can return the data in json format, should succeed
        #. Check if you can return the data in yaml format, should succeed
        """

        country_code = j.data.idgenerator.generateXCharID(10)
        schema, model = self.getSchemaAndModel(country_code=country_code)

        author = self.getNewUser()
        # . Register user1's data as public, should succeed
        data_id1 = j.clients.tfgrid_registry.register(
            schema=schema, authors=[author.tid], model=model, is_encrypted_data=False
        )
        self.assertTrue(data_id1, "Failed to register your content")

        # . Check if you can return the data in json format, should succeed
        res = j.clients.tfgrid_registry.find_formatted(registered_info_format="json")
        data_dict = j.data.serializers.json.loads(res)
        self.assertEqual(type(data_dict), type({}))

        # . Check if you can return the data in yaml format, should succeed
        res = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml")
        data_dict = j.data.serializers.yaml.loads(res)
        self.assertEqual(type(data_dict), type({}))

    ## To Do
    # Do more tests for complicated scenarios
    # filter using diiferent fields, when this:https://github.com/threefoldtech/jumpscaleX_core/issues/217 is done


