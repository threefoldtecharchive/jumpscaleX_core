import unittest
from Jumpscale import j
from base_test import BaseTest


class SonicClient(BaseTest):
    @classmethod
    def setUpClass(cls):
        cls.info("install sonic builder")
        j.builders.apps.sonic.install()

        cls.info("Start Sonic server")
        j.servers.sonic.default.start()

        cls.info("create a Sonic client")
        cls.client = j.clients.sonic.get("test", host="127.0.0.1", port=1491, password="123456")

    def setUp(self):
        print("\t")
        self.info("Test case : {}".format(self._testMethodName))

        RAND_NUM = self.rand_num()
        self.sub_word = "comman"
        self.RAND_STRING_1 = self.rand_string()
        self.RAND_STRING_2 = self.sub_word + self.rand_string()
        self.RAND_STRING_3 = self.sub_word + self.rand_string()

        self.data = {
            "post:1": "{}".format(self.RAND_STRING_1),
            "post:2": "{}".format(self.RAND_STRING_1),
            "post:3": "{}".format(self.RAND_STRING_1),
            "post:4": "{}".format(self.RAND_STRING_2),
            "post:5": "{}".format(self.RAND_STRING_3),
        }

        self.COLLECTION = "COLL_{}".format(RAND_NUM)
        self.BUCKET = "BUCKET_{}".format(RAND_NUM)

        self.info("Push data to sonic server")
        for article_id, content in self.data.items():
            self.flag = self.client.push(self.COLLECTION, self.BUCKET, article_id, content)

    def tearDown(self):
        self.info("Flush all data in {} collection".format(self.COLLECTION))
        self.client.flush(self.COLLECTION)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/271")
    def test001_push_with_collection_and_bucket(self):
        """
        TC 522
        Test case to Push method in Sonic client, with valid collection, bucket, object, text.

        **Test scenario**
        #. Push data to sonic server
        #. Check the count of indexed search data in the collection and bucket, should equal to length of data.
        #. Use count method with non valid collection and bucket name, the output should be 0.
        """

        self.assertTrue(self.flag)

        self.info("check the count of indexed search data in the collection and bucket")
        self.assertEquals(self.client.count(self.COLLECTION, self.BUCKET), len(self.data))

        self.info("Use count method non valid collection and bucket name, the output should equal to 0")
        self.assertEqual(self.client.count("RANDOM_COLLECTION", "RANDOM_BUCKET"), 0)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/272")
    def test002_query_for_certain_collection_and_bucket(self):
        """
        TC 526
        Test Case to query method with certain collection and data.

        **Test scenario**
        #. Push data to sonic server
        #. Query to certain data with valid collection and bucket name.
        #. Query to certain data with non valid collection and bucket name.
        """

        self.info("Query to certain data with valid collection and bucket name, and check the output.")
        self.assertEqual(
            sorted(self.client.query(self.COLLECTION, self.BUCKET, self.RAND_STRING_1)), ["post:1", "post:2", "post:3"]
        )

        # need to check the correct behaviour for this query.
        self.info("Query for non valid collection and bucket, should raise an error")
        self.assertEqual(len(self.client.query("RANDOM_COLLECTION", "RANDOM_BUCKET", self.rand_string())), 0)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/272")
    def test003_suggest_with_certain_collection_and_bucket(self):
        """
        TC 528
        Test Case to suggest with certain collection and bucket name.

        **Test scenario**
        #. Push data to sonic server
        #. Use suggest method with valid collection and bucket name.
        #. Use suggest method with non valid collection and bucket name.
        """

        self.info("Use suggest method with valid collection and bucket name")
        self.assertEqual(
            sorted(self.client.suggest(self.COLLECTION, self.BUCKET, self.sub_word)),
            [self.RAND_STRING_2, self.RAND_STRING_3],
        )

        # need to check the correct behaviour for this query.
        self.info("Use suggest method with non valid collection and bucket name")
        self.assertIn("PENDING", self.client.suggest("RANDOM_COLLECTION", "RANDOM_COLLECTION", self.rand_string()))

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/272")
    def test004_pop_with_certain_collection_and_bucket(self):
        """
        TC 532
        Test Case to pop method with certain collection and bucket.

        **Test scenario**
        #. Push data to sonic server
        #. Use pop method with non valid data, the count of data shouldn't change.
        #. Use pop method to pop certain index, the output shouldn't be 0.
        #. Use count method to check that output, should equal to the length of tha original data -1.
        """
        self.info("Use pop method with non valid data, the count of data shouldn't change")
        self.client.pop(self.COLLECTION, self.BUCKET, "post:15", "test")

        self.info("Use pop method to pop an object")
        self.client.pop(self.COLLECTION, self.BUCKET, "post:2", "{}".format(self.RAND_STRING_1))

        self.info("Use count method to check the length of data after pop")
        self.assertEqual(self.client.count(self.COLLECTION, self.BUCKET), len(self.data) - 1)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/272")
    def test005_flush_for_certain_collection_and_bucket(self):
        """
        TC 534
        Test Case to flush for certain collection.

        **Test scenario**
        #. Push data to sonic server
        #. Flush certain collection.
        #. Use count method to check that output, should be 0.
        """

        self.info("Flush certain collection")
        self.client.flush(self.COLLECTION)

        self.info("Use count method to check the length of data after flush, should be 0")
        self.assertEqual(self.client.count(self.COLLECTION, self.BUCKET), 0)

        # self.info("Use flush to flush non existing collection with certain bucket")
        # self.client.flush("RANDOM_COLLECTION", "RANDOM_BUCKET")

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/272")
    def test007_flush_object_using_collection_bucket(self):
        """
        TC 536
        Test Case for flush_object method for certain object in certain collection with certain bucket.

        **Test scenario**
        #. Push data to sonic server
        #. Use flush_object to flush certain object in collection with certain bucket.
        #. Use query to check that this record is flushed.
        """
        self.info("Use flush_object to flush certain object in collection with certain bucket")
        self.client.flush_object(self.COLLECTION, self.BUCKET, "post:4")

        self.info("Use query to check that this record is flushed")
        self.assertEqual(self.client.query(self.COLLECTION, self.BUCKET, self.sub_word), ["post:5"])

        # self.info("Use flush_object to flush non existing object in collection with certain bucket")
        # self.client.flush_object("RANDOM_COLLECTION", "RANDOM_BUCKET", "RANDOM_OBJECT")

    def test007_flush_bucket_for_certain_collection(self):
        """
        TC 538
        Test Case for flush_object method for certain bucket in certain collection.

        **Test scenario**
        #. Push data to sonic server
        #. Use flush_bucket method to flush certain bucket.
        #. Check that there is no more objects in the bucket.
        """

        self.info("use flush_bucket method to flush certain bucket")
        self.client.flush_bucket(self.COLLECTION, self.BUCKET)

        self.info("Check count in {} bucket, should be 0".format(self.BUCKET))
        self.assertEqual(self.client.count(self.COLLECTION, self.BUCKET), 0)
