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
        cls.client = j.clients.sonic.get('test', host="127.0.0.1", port=1491, password='123456')

    def setUp(self):
        print('\t')
        self.info('Test case : {}'.format(self._testMethodName))

        RAND_NUM = self.rand_num()
        self.RAND_STRING_1 = self.rand_string(10)
        self.RAND_STRING_2 = self.rand_string(15)

        self.data = {
            'post:1': "this is some test {}, for love of JSX".format(self.RAND_STRING_1),
            'post:2': 'this is a hello {}'.format(self.RAND_STRING_2),
            'post:3': "hello {}?".format(self.RAND_STRING_1),
            'post:4': "for the love of {}?".format(self.RAND_STRING_2),
            'post:5': "for the lord of {}".format(RAND_NUM)
        }

        self.COLLECTION = "COLL_{}".format(RAND_NUM)
        self.BUCKET = "BUCKET_{}".format(RAND_NUM)

        self.info("push the data to sonic server")
        for article_id, content in self.data.items():
            self.client.push(self.COLLECTION, self.BUCKET, article_id, content)

    def tearDown(self):
        self.info("Flush all data in {} collection, and {} bucket".format(self.COLLECTION, self.BUCKET))
        self.client.flush(self.COLLECTION)

    def test001_push_with_collection_and_bucket(self):
        """
        TC 522
        Test case to Push method in Sonic client, with valid collection, bucket, object, text.

        **Test scenario**
        #. Check the count of indexed search data in the collection and bucket, should equal to length of data.
        """

        self.info("check the count of indexed search data in the collection and bucket")
        self.assertEquals(self.client.count(self.COLLECTION, self.BUCKET), len(self.data))

    def test002_query_for_certain_collection_and_bucket(self):
        """
        TC 526
        Test Case to query method with certain collection and data.

        **Test scenario**
        #. Query to certain data with valid collection and bucket name.
        #. Query to certain data with non valid collection and bucket name.
        """

        self.info("Query to certain data with valid collection and bucket name, and check the output.")
        self.assertEqual(
            sorted(self.client.query(self.COLLECTION, self.BUCKET, self.RAND_STRING_1)), ['post:1', 'post:3']
        )

        # need to check the correct behaviour for this query.
        self.info("Query for non valid collection and bucket, should raise an error")
        self.assertEqual(len(self.client.query("RANDOM_COLLECTION", "RANDOM_BUCKET", "RANDOM_OBJECT")), 0)

    def test003_suggest_with_certain_collection_and_bucket(self):
        """
        TC 528
        Test Case to suggest with certain collection and bucket name.

        **Test scenario**
        #. Use suggest method with valid collection and bucket name.
        #. Use suggest method with non valid collection and bucket name.
        """

        self.info("Use suggest method with valid collection and bucket name")
        self.assertEqual(
            sorted(self.client.suggest(self.COLLECTION, self.BUCKET, "lo")), ['lord', 'love']
        )

        # need to check the correct behaviour for this query.
        self.info("Use suggest method with non valid collection and bucket name")
        self.assertIn('PENDING', self.client.suggest("RANDOM_COLLECTION", "RANDOM_COLLECTION", "RANDOM"))

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/272")
    def test004_count_with_non_valid_collection_and_bucket(self):
        """
        TC 531
        Test Case to count method with non valid collection and bucket name.

        **Test scenario**
        #. Use count method with non valid collection and bucket name, the output should be 0.
        """
        self.info("Use count method non valid collection and bucket name, the output should equal to 0")
        self.assertEqual(self.client.count("RANDOM_COLLECTION", "RANDOM_BUCKET"), 0)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/272")
    def test005_pop_with_certain_collection_and_bucket(self):
        """
        TC 532
        Test Case to pop method with certain collection and bucket.

        **Test scenario**
        #. Use pop method with non valid data, the count of data shouldn't change.
        #. Use pop method to pop certain index, the output shouldn't be 0.
        #. Use count method to check that output, should equal to the length of tha original data -1.
        """
        self.info("Use pop method with non valid data, the count of data shouldn't change")
        self.client.pop(self.COLLECTION, self.BUCKET, 'post:15', "test")

        self.info("Use pop method to pop an object")
        self.client.pop(self.COLLECTION, self.BUCKET, 'post:2', 'this is a hello {}'.format(self.RAND_STRING_2))

        self.info("Use count method to check that output")
        self.assertEqual(self.client.count(self.COLLECTION, self.BUCKET), len(self.data)-1)

    def test006_flush_for_certain_collection_and_bucket(self):
        """
        TC 534
        Test Case to flush for certain collection.

        **Test scenario**
        #. Use flush to flush certain collection.
        #. Use count method to check that output, should be 0.
        """

        self.info("Use flush to flush certain collection with certain bucket")
        self.client.flush(self.COLLECTION)

        self.info("Use count method to check that output")
        self.assertEqual(self.client.count(self.COLLECTION, self.BUCKET), 0)

        # self.info("Use flush to flush non existing collection with certain bucket")
        # self.client.flush("RANDOM_COLLECTION", "RANDOM_BUCKET")

    def test007_flush_object_method_for_certain_object_in_certain_collection_with_certain_bucket(self):
        """
        TC 536
        Test Case for flush_object method for certain object in certain collection with certain bucket.

        **Test scenario**
        #. Use flush_object to flush certain object in collection with certain bucket.
        #. Use query to check that this record is flushed.
        """
        self.info("Use flush_object to flush certain object in collection with certain bucket")
        self.client.flush_object(self.COLLECTION, self.BUCKET, 'post:4')

        self.info("Use query to check that this record is flushed")
        self.assertEqual(self.client.query(self.COLLECTION, self.BUCKET, "love"), ['post:1'])

        # self.info("Use flush_object to flush non existing object in collection with certain bucket")
        # self.client.flush_object("RANDOM_COLLECTION", "RANDOM_BUCKET", "RANDOM_OBJECT")

    def test008_flush_bucket_for_certain_bucket_in_certain_collection(self):
        """
        TC 538
        Test Case for flush_object method for certain bucket in certain collection.

        **Test scenario**
        #. use flush_bucket method to flush certain bucket.
        #. Check that their is no more objects in the second created bucket.
        """

        self.info("use flush_bucket method to flush certain bucket")
        self.client.flush_bucket(self.COLLECTION, self.BUCKET)

        self.info("Check count in {} bucket, should be 0".format(self.BUCKET))
        self.assertEqual(self.client.count(self.COLLECTION, self.BUCKET), 0)
