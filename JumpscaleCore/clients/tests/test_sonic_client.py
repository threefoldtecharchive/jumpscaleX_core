import unittest
from Jumpscale import j
from random import randint
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

        self.data = {
            'post:1': "this is some test text hello",
            'post:2': 'this is a hello world post',
            'post:3': "hello how is it going?",
            'post:4': "for the love of god?",
            'post:5': "for the love of a lord?",
        }

        self.COLLECTION = "COLL_{}".format(randint(1, 1000))
        self.BUCKET = "BUCKET_{}".format(randint(1, 1000))

    def tearDown(self):
        self.info("Flush all data in {} collection, and {} bucket".format(self.COLLECTION, self.BUCKET))
        self.client.flush(self.COLLECTION, self.BUCKET)

    @classmethod
    def TearDownClass(cls):
        cls.info("Stop Sonic server")
        j.servers.sonic.default.stop()

        cls.info("Uninstall Sonic builder")
        j.builders.apps.sonic.uninstall()

    def test001_push(self):
        """
        TC 522
        Test Case to test Push method in Sonic client, with valid collection, bucket, object, text.

        **Test scenario**
        #. Push the data to sonic server.
        #. Check the count of indexed search data in the collection and bucket, should equal to 6.
        """

        self.info("push the data to sonic server")
        for article_id, content in self.data.items():
            self.assertTrue(self.client.push(self.COLLECTION, self.BUCKET, article_id, content))

        self.info("check the count of indexed search data in the collection and bucket")
        self.assertEquals(self.client.count(self.COLLECTION, self.BUCKET), 6)

    def test002_push_without_collection_or_bucket(self):
        """
        TC 523
        Test Case to test push method without collection and bucket.

        **Test scenario**
        #. Test push method without collection and bucket.
        """

        self.info("Test push method without collection and bucket")
        with self.assertRaises(Exception):
            self.client.push('post_1', "test should fail")
    #
    # def test003_push_with_diff_collection_and_bucket(self):
    #     """
    #     TC 524
    #     Test Case to push method with different collection and bucket.
    #
    #     **Test scenario**
    #     #. Push the data to sonic server.
    #     #. Check the count of indexed search data in the collection and bucket, should equal to 6.
    #     #. Redo step 1 again, with different collection and bucket.
    #     #. Check again the number of indexed data in the second collection and bucket, should equal to 2.
    #     """
    #
    #     self.info("Push the data to sonic server")
    #     for article_id, content in self.data.items():
    #         self.assertTrue(self.client.push(self.COLLECTION, self.BUCKET, article_id, content))
    #
    #     self.info("Check the count of indexed search data in the collection and bucket")
    #     self.assertEquals(self.client.count(self.COLLECTION, self.BUCKET), 6)
    #
    #     self.info("Push the data to sonic server, with different collection and bucket name")
    #     collection_new = "COLL_{}".format(randint(1, 1000))
    #     bucket_new = "BUCKET_{}".format(randint(1, 1000))
    #     self.client.push(collection_new, bucket_new, "post_1", "test push with different data")
    #
    #     self.info("Check the count of indexed search data in the new collection and bucket")
    #     self.assertEquals(self.client.count(collection_new, bucket_new), 2)

    def test004_query_with_exists_collection_and_bucket(self):
        """
        TC 526
        Test Case to test query with an exists collection and bucket name.

        **Test scenario**
        #. Push the data to sonic server.
        #. Query to those data, and check the output.
        """

        self.info("Push the data to sonic server")
        for article_id, content in self.data.items():
            self.assertTrue(self.client.push(self.COLLECTION, self.BUCKET, article_id, content))

        # self.assertEqual(len(self.client.query(self.COLLECTION, self.BUCKET, "love")), 2)
        self.assertEqual(
            sorted(self.client.query(self.COLLECTION, self.BUCKET, "love")), sorted(['post:5', 'post:4'])
        )

    def test005_query_with_non_exists_collection_and_bucket(self):
        """
        TC 527
        Test Case to test query with non exists collection and bucket.

        **Test scenario**
        #. Query for non exists collection and bucket.
        """

        self.info("Query for non exists collection and bucket.")
        self.assertEqual(len(self.client.query("RANDOM_COLLECTION", "RANDOM_BUCKET", "test")), 0)

    def test006_suggest_with_exists_collection_and_bucket(self):
        """
        TC 528
        Test Case to test suggest with an exists collection and bucket name.

        **Test scenario**
        #. Push the data to sonic server.
        #. Use suggest method and check the output.
        """
        self.info("Push the data to sonic server")
        for article_id, content in self.data.items():
            self.assertTrue(self.client.push(self.COLLECTION, self.BUCKET, article_id, content))

        self.info("Use suggest method and check the output")
        # self.assertEquals(self.client.suggest(self.COLLECTION, self.BUCKET, "lo"), 2)
        self.assertEqual(
            sorted(self.client.suggest(self.COLLECTION, self.BUCKET, "lo")), sorted(['lord', 'love'])
        )

    def test007_suggest_with_non_exists_collection_and_bucket(self):
        """
        TC 529
        Test Case to test with non exists collection and bucket name.

        **Test scenario**
        #. Use suggest method with non exists collection and bucket name, should return PENDING.
        """
        self.info("Use suggest method with non exists collection and bucket name")
        self.assertIn('PENDING', self.client.suggest("RANDOM_COLLECTION", "RANDOM_COLLECTION", "RANDOM"))

    # def test008_count_for_exists_collection_and_bucket(self):
    #     """
    #     TC 530
    #     Test Case to test count method with exists collection and bucket name.
    #
    #     **Test scenario**
    #     #. Push the data to sonic server.
    #     #. Use count method with exists collection and bucket name, the output should be 6.
    #     """
    #     self.info("Push the data to sonic server")
    #     for article_id, content in self.data.items():
    #         self.assertTrue(self.client.push(self.COLLECTION, self.BUCKET, article_id, content))
    #
    #     self.info("check the count of indexed search data in the collection and bucket")
    #     self.assertEquals(self.client.count(self.COLLECTION, self.BUCKET), 6)

    # def test009_count_for_exists_collection_and_bucket(self):
    #     """
    #     TC 531
    #     Test Case to test count method with non exists collection and bucket name.
    #
    #     **Test scenario**
    #     #. Use count method with exists collection and bucket name, the output should equal to 0.
    #     """
    #     self.info("Use count method with exists collection and bucket name, the output should equal to 0")
    #     self.assertEqual(self.client.count("RANDOM_COLLECTION", "RANDOM_BUCKET"), 0)

    def test010_pop_for_exists_collection_and_bucket(self):
        """
        TC 532
        Test Case to test pop method with exists collection and bucket.

        **Test scenario**
        #. Push the data to sonic server.
        #. Use pop method to pop the latest index, the output shouldn't equal to 0.
        #. Use count method to check that output, should equal to 5.
        """
        self.info("Push the data to sonic server")
        for article_id, content in self.data.items():
            self.assertTrue(self.client.push(self.COLLECTION, self.BUCKET, article_id, content))

        self.info("Use pop method to pop the latest index")
        # self.assertNotEquals(self.client.pop(self.COLLECTION, self.BUCKET, 'post:5', "for the love lord?"), 0)

        self.info("Use count method to check that output")
        self.assertEqual(self.client.count(self.COLLECTION, self.BUCKET), 5)

    def test011_pop_for_non_exists_collection_and_bucket(self):
        """
        TC 533
        Test Case to test pop method with non exists collection and bucket.

        **Test scenario**
        #. Use pop method to pop the latest index, the output should equal to 0.
        """
        self.info("Use pop method to pop the latest index")
        self.assertEqual(self.client.pop("RANDOM_COLLECTION", "RANDOM_BUCKET", 'test', "test"), 0)

    def test012_flush_for_exists_collection_and_bucket(self):
        """
        TC 534
        Test Case to test flush for exists collection and bucket.

        **Test scenario**
        #. Push the data to sonic server.
        #. Use flush to flush certain collection with certain bucket.
        #. Use count method to check that output, should equal to 0.
        """
        self.info("Push the data to sonic server")
        for article_id, content in self.data.items():
            self.assertTrue(self.client.push(self.COLLECTION, self.BUCKET, article_id, content))

        self.info("Use flush to flush certain collection with certain bucket")
        # self.assertNotEquals(self.client.flush(self.COLLECTION, self.BUCKET), 0)

        self.info("Use count method to check that output")
        self.assertEqual(self.client.count(self.COLLECTION, self.BUCKET), 0)

    def test013_flush_for_non_exists_collection_and_bucket(self):
        """
        TC 535
        Test Case for flush method for non exists collection and method.

        **Test scenario**
        #. Use flush to flush non exists collection with certain bucket.
        """
        self.info("Use flush to flush non exists collection with certain bucket")
        self.assertEquals(self.client.flush("RANDOM_COLLECTION", "RANDOM_BUCKET"), 0)

    def test014_flush_object_method_for_exists_object_in_certain_collection_with_certain_bucket(self):
        """
        TC 536
        Test Case for flush_object method for certain object in certain collection with certain bucket.

        **Test scenario**
        #. Push the data to sonic server.
        #. Use flush_object to flush certain object in collection with certain bucket.
        #. Use query to check that this record is flushed.
        """
        self.info("Push the data to sonic server")
        for article_id, content in self.data.items():
            self.assertTrue(self.client.push(self.COLLECTION, self.BUCKET, article_id, content))

        self.info("Use flush_object to flush certain object in collection with certain bucket")
        self.assertNotEqual(self.client.flush_object(self.COLLECTION, self.BUCKET, 'post:4'), 0)

        self.info("Use query to check that this record is flushed")
        self.assertEqual(self.client.query(self.COLLECTION, self.BUCKET, "love"), ['post:5'])

    def test015_flush_object_method_for_non_exists_object_in_certain_collection_with_certain_bucket(self):
        """
        TC 537
        Test Case for flush_object for non exists object.

        **Test scenario**
        #. Use flush_object to flush non exists object in collection with certain bucket.
        """
        self.info("Use flush_object to flush non exists object in collection with certain bucket")
        self.assertEqual(self.client.flush_object("RANDOM_COLLECTION", "RANDOM_BUCKET", "RANDOM_OBJECT"), 0)

    def test016_flush_bucket_for_exists_bucket_in_certain_collection(self):
        """
        TC 538
        Test Case for flush_object method for certain bucket in certain collection.

        **Test scenario**
        #. Push the data to sonic server.
        #. Push data to another bucket within the same collection.
        #. Check that their is no more objects in the second created bucket.

        """
        self.info("Push the data to sonic server")
        for article_id, content in self.data.items():
            self.assertTrue(self.client.push(self.COLLECTION, self.BUCKET, article_id, content))

        self.info("Push data to another bucket within the same collection")
        self.assertTrue(self.client.push(self.COLLECTION, "posts_1", "test", "test for flush_bucket"))

        self.info("Check that there are no more objects in the second created bucket")
        self.assertEqual(self.client.count(self.COLLECTION, "posts_1"), 0)

        self.info("Check that there are objects in the first created bucket")
        self.assertEqual(self.client.count(self.COLLECTION, self.BUCKET), 6)










