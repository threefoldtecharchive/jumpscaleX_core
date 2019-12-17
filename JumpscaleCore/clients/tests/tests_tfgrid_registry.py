from Jumpscale import j
from unittest import skip
from base_test import BaseTest
from parameterized import parameterized


class RegistryTests(BaseTest):

    bcdb = j.data.bcdb.get("threebot_registery")

    @classmethod
    def setUpClass(cls):
        try:    
            cls.cl = cls.addRegistryPackage()
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        j.servers.threebot.default.stop()
        j.sal.process.killall("tmux")

    @classmethod
    def addRegistryPackage(cls):
        # . Start threebot server, add registery package, then reload the client.
        cl = j.servers.threebot.local_start_default(background=True)
        cl = j.clients.gedis.get("threebot_registery", port=8901)
        cl.actors.package_manager.package_add(
            path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/registry"
        )
        cl.reload()
        return cl

    def getNewUser(self):
        tid = j.data.idgenerator.generateRandomInt(1000, 9000)
        randStr = j.data.idgenerator.generateXCharID(10)
        return j.tools.threebot.me.get(randStr, tid=tid, email=randStr + "@test.com", tname=randStr + "_name")

    def getSchemaAndModel(self, x="hello"):
        schema = """
            @url = threebot.registry.test.schema.1 
            url = "" 
            x = ""
            tags = (LS)
        """
        randStr = j.data.idgenerator.generateXCharID(10)
        scm = j.data.schema.get_from_text(schema)
        model = self.bcdb.model_get(url=scm.url).new()
        model.url = randStr + ".com"
        model.x = x
        model.save()
        return schema, model

    def register_using_filter(self, filter, **kwargs):
        filter_value = j.data.idgenerator.generateRandomInt(1000, 2000)

        if filter == "country_code":
            j.clients.tfgrid_registry.register(country_code=filter_value, **kwargs)

        elif filter == "topic":
            filter_value = "TRAVEL"
            j.clients.tfgrid_registry.register(country_code="234", topic=filter_value, **kwargs)

        elif filter == "location_latitude":
            j.clients.tfgrid_registry.register(country_code="234", location_latitude=filter_value, **kwargs)

        else:
            j.clients.tfgrid_registry.register(country_code="234", location_longitude=filter_value, **kwargs)

        return filter_value

    def find_using_filter(self, filter, filter_value):

        if filter == "country_code":
            res = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml", country_code=filter_value)

        elif filter == "topic":
            res = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml", topic=filter_value)

        elif filter == "location_latitude":
            res = j.clients.tfgrid_registry.find_formatted(
                registered_info_format="yaml", location_latitude=filter_value
            )

        else:
            res = j.clients.tfgrid_registry.find_formatted(
                registered_info_format="yaml", location_longitude=filter_value
            )

        data = j.data.serializers.yaml.loads(res)
        return data

    def test001_RegisterationAndPrivacy(self):
        """TC560
        #. Start threebot server, add registery package, then reload the client.
        #. Register user1's data as public, should succeed
        #. Get user1's public data, should succeed
        #. Register user1's data as private with giving access to user2, should succeed
        #. Get data with user 2, should succeed
        #. Get data with unauthorized data, should not be able to get the data
        """

        self.info("Test case : {}".format(self._testMethodName))
        country_code = j.data.idgenerator.generateXCharID(10)
        schema, model = self.getSchemaAndModel()
        author = self.getNewUser()
        authorized_reader = self.getNewUser()
        unauthorized_reader = self.getNewUser()

        self.info("Register user1's data as public, should succeed")
        data_id1 = j.clients.tfgrid_registry.register(
            schema=schema, authors=[author.tid], model=model, is_encrypted_data=False, country_code=country_code
        )
        self.assertTrue(data_id1, "Failed to register content")

        self.info("Get user1's public data, should succeed")
        data = j.clients.tfgrid_registry.get_data_by_id(data_id1, author.tid)
        self.assertEqual(model, data)

        self.info("Register user1's data as private with giving access to user2, should succeed")
        data_id2 = j.clients.tfgrid_registry.register(
            schema=schema,
            authors=[author.tid],
            model=model,
            is_encrypted_data=True,
            readers=[authorized_reader.tid],
            country_code=country_code,
        )
        self.assertTrue(data_id2, "Failed to register content")

        self.info("Get data with user 2, should succeed")
        data = j.clients.tfgrid_registry.find_encrypted(authorized_reader.tid)
        self.assertEqual(model, data[-1])

        self.info("Get data with unauthorized data, should not be able to get the data")
        data = j.clients.tfgrid_registry.find_encrypted(unauthorized_reader.tid)
        self.assertFalse(data)

    def test002_CheckOnDataFormat(self):
        """TC561
        #. Start threebot server, add registery package, then reload the client.
        #. Register user1's data
        #. Check if you can load the data in json format, should succeed
        #. Check if you can load the data in yaml format, should succeed
        """

        self.info("Test case : {}".format(self._testMethodName))
        self.info("Register user1's data as public")
        schema, model = self.getSchemaAndModel()
        author = self.getNewUser()
        data_id1 = j.clients.tfgrid_registry.register(
            schema=schema, authors=[author.tid], model=model, is_encrypted_data=False, country_code="2354"
        )
        self.assertTrue(data_id1, "Failed to register your content")

        self.info("Check if you can return the data in json format, should succeed")
        res = j.clients.tfgrid_registry.find_formatted(registered_info_format="json")
        data = j.data.serializers.json.loads(res)
        self.assertTrue(data)

        self.info("Check if you can return the data in yaml format, should succeed")
        res = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml")
        data = j.data.serializers.yaml.loads(res)
        self.assertTrue(data)

    @parameterized.expand(["country_code", "location_latitude", "location_longitude"])
    def test003_search_using_single_filter(self, filter):
        """TC562
        #. Start threebot server, add registery package, then reload the client.
        #. Register user1's data (D1) with adding filter
        #. Get the data using that filter, should succeed
        #. Register user1's different data (D2) with adding same filter
        #. Get data using filter F1, should return D1 and D2
        """

        self.info("Test case : {}".format(self._testMethodName))
        self.info("Register user1's data (D1) with adding filter")
        x = j.data.idgenerator.generateXCharID(10)
        schema, model = self.getSchemaAndModel(x)
        author = self.getNewUser()
        filter_value = self.register_using_filter(filter, schema=schema, authors=[author.tid], model=model)

        self.info("Get the data using that filter, should succeed")
        data = self.find_using_filter(filter, filter_value)
        self.assertEqual(len(data), 1, "couldn't filter using country code")
        self.assertEqual(data[0]["x"], x)

        self.info("Register user1's different data (D2) with adding same filter")
        x2 = j.data.idgenerator.generateXCharID(10)
        schema, model = self.getSchemaAndModel(x2)
        filter_value = self.register_using_filter(filter, schema=schema, authors=[author.tid], model=model)

        self.info("Get data using filter F1, should return D1 and D2")
        data2 = self.find_using_filter(filter, filter_value)
        self.assertNotEqual(len(data2), 2)

    def test004_search_using_two_filters(self):
        """TC563
        #. Start threebot server, add registery package, then reload the client.
        #. Register user1's data (D1) with adding country_code (C1)
        #. Register user1's data (D2) with adding topic (T1) ans same country code (C1)
        #. Get data using filter C1, should get D1 and D2
        #. Get data using filters T1 and C1, should only get D2
        """

        self.info("Test case : {}".format(self._testMethodName))
        self.info("Register user1's data (D1) with adding country_code (C1)")
        x = j.data.idgenerator.generateXCharID(10)
        schema, model = self.getSchemaAndModel(x)
        author = self.getNewUser()
        C1 = self.register_using_filter("country_code", schema=schema, authors=[author.tid], model=model)

        self.info("Register user1's data (D2) with adding topic (T1) and same country code (C1)")
        x2 = j.data.idgenerator.generateXCharID(10)
        schema, model = self.getSchemaAndModel(x2)
        T1 = "TRAVEL"
        j.clients.tfgrid_registry.register(schema=schema, authors=[author.tid], model=model, country_code=C1, topic=T1)

        self.info("Get data using filter C1, should get D1 and D2")
        data = self.find_using_filter("country_code", C1)
        self.assertEqual(len(data), 2)
        lst = [obj["x"] for obj in data]
        self.assertIn(x, lst)
        self.assertIn(x2, lst)

        self.info("Get data using filters T1 and C1, should only get D2")
        res2 = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml", country_code=C1, topic=T1)
        data2 = j.data.serializers.yaml.loads(res2)
        self.assertNotEqual(len(data2), 1)
        self.assertEqual(data2[1]["x"], x2)
