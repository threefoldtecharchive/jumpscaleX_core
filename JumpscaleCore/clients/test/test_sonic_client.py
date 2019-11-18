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
        #. push the data to sonic server.
        #. check the count of indexed search data in the collection and bucket, should equal to 6.
        """

        self.info("push the data to sonic server")
        for article_id, content in self.data.items():
            self.client.push(self.COLLECTION, self.BUCKET, article_id, content)

        self.info("check the count of indexed search data in the collection and bucket")
        self.assertEquals(self.client.count(self.COLLECTION, self.BUCKET), 6)

    def test002_push_without_collection_or_bucket(self):
        """
        TC 523
        Test Case to test push method without collection and bucket, should fail.

        **Test scenario**
        #. Test push method without collection and bucket.
        """

        self.info("Test push method without collection and bucket")
        with self.assertRaises(Exception):
            self.client.push('post_1', "test should fail")

    def test003_push_with_diff_collection_and_bucket(self):
        """
        TC 524
        Test Case to push method with different collection and bucket, should success.

        **Test scenario**
        #. push the data to sonic server.
        #. check the count of indexed search data in the collection and bucket, should equal to 2.
        #. redo step 1 again, with different collection and bucket.
        #. check again the number of indexed data in the second collection and bucket, should equal to 2.
        """

        self.info("push the data to sonic server")
        for article_id, content in self.data.items():
            self.client.push(self.COLLECTION, self.BUCKET, article_id, content)

        self.info("check the count of indexed search data in the collection and bucket")
        self.assertEquals(self.client.count(self.COLLECTION, self.BUCKET), 6)

        self.info("push the data to sonic server, with different collection and bucket name")
        collection_new = "COLL_{}".format(randint(1, 1000))
        bucket_new = "BUCKET_{}".format(randint(1, 1000))
        self.client.push(collection_new, bucket_new, "post_1", "test push with different data")

        self.info("check the count of indexed search data in the new collection and bucket")
        self.assertEquals(self.client.count(collection_new, bucket_new), 2)

    def test004_query_with_exists_collection_and_bucket(self):
        """
        TC 526
        Test Case to test query with an exists collection and bucket name, should success.

        **Test scenario**
        #. push the data to sonic server.
        #. query to those data, and check the output.
        """

        self.info("push the data to sonic server")
        for article_id, content in self.data.items():
            self.client.push(self.COLLECTION, self.BUCKET, article_id, content)

