import time
from Jumpscale import j


def info(message):
    j.tools.logger._log_info(message)


def rand_string():
    return j.data.idgenerator.generateXCharID(10)


def rand_num(start=100, stop=1000):
    return j.data.idgenerator.generateRandomInt(start, stop)


skip = j.baseclasses.testtools._skip


client = ""
COLLECTION = ""
flag = ""
BUCKET = ""
data = {}
RAND_STRING_1 = ""
sub_word = ""
RAND_STRING_2 = ""
RAND_STRING_3 = ""


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/250")
def before_all():
    info("install sonic builder")
    j.builders.apps.sonic.install()

    info("Start Sonic server")
    j.servers.sonic.default.start()

    info("create a Sonic client")
    global client
    client = j.clients.sonic.get("test", host="127.0.0.1", port=1491, password="123456")


def before():
    RAND_NUM = rand_num()
    RAND_STRING = rand_string()
    global sub_word
    sub_word = "comman"
    global RAND_STRING_1, RAND_STRING_2, RAND_STRING_3
    RAND_STRING_1 = rand_string()
    RAND_STRING_2 = sub_word + rand_string()
    RAND_STRING_3 = sub_word + rand_string()

    global data
    data = {
        "post:1": "{}".format(RAND_STRING_1),
        "post:2": "{}".format(RAND_STRING_2),
        "post:3": "{}".format(RAND_STRING_3),
    }

    global COLLECTION
    COLLECTION = "COLL_{}".format(RAND_NUM)
    global BUCKET
    BUCKET = "BUCKET_{}".format(RAND_NUM)

    info("Push data to sonic server")
    global flag
    for article_id, content in data.items():
        flag = client.push(COLLECTION, BUCKET, article_id, content)


def after():
    info("Flush all data in {} collection".format(COLLECTION))
    client.flush(COLLECTION)


def after_all():
    j.servers.sonic.default.stop()


def test001_push_collection_bucket():
    """
    TC 522
    Test case to Push method in Sonic client, with valid collection, bucket, object, text.

    **Test scenario**
    #. Push data to sonic server
    #. Check the count of indexed search data in the collection and bucket, should equal to length of data.
    #. Use count method with non valid collection and bucket name, the output should be 0.
    """

    assert flag
    import ipdb; ipdb.set_trace()
    info("check the count of indexed search data in the collection and bucket")
    assert client.count(COLLECTION, BUCKET) == len(data) + 1

    info("Use count method non valid collection and bucket name, the output should equal to 0")
    assert client.count(rand_string(), rand_string()) == 0


# def test002_query_collection_bucket():
#     """
#     TC 526
#     Test Case to query method with certain collection and data.
#
#     **Test scenario**
#     #. Push data to sonic server
#     #. Query to certain data with valid collection and bucket name.
#     #. Query to certain data with non valid collection and bucket name.
#     """
#
#     info("Query to certain data with valid collection and bucket name, and check the output.")
#     assert sorted(client.query(COLLECTION, BUCKET, RAND_STRING_1)) == ["post:1"]
#
#     info("Query for non valid collection and bucket, should raise an error")
#     assert len(client.query(rand_string(), rand_string(), rand_string())) == 0
#
#
# def test003_suggest_collection_bucket():
#     """
#     TC 528
#     Test Case to suggest with certain collection and bucket name.
#
#     **Test scenario**
#     #. Push data to sonic server
#     #. Use suggest method with valid collection and bucket name.
#     #. Use suggest method with non valid collection and bucket name.
#     """
#
#     info("Use suggest method with valid collection and bucket name")
#     assert sorted(client.suggest(COLLECTION, BUCKET, sub_word)) == [RAND_STRING_2, RAND_STRING_3]
#
#     info("Use suggest method with non valid collection and bucket name")
#     assert "PENDING" in client.suggest(rand_string(), rand_string(), rand_string())
#
#
# def test004_pop_collection_bucket():
#     """
#     TC 532
#     Test Case to pop method with certain collection and bucket.
#     **Test scenario**
#     #. Push data to sonic server.
#     #. Use flush to remove certain object.
#     #. Use pop to get the object back, and check the existing of this object.
#     #. Use pop method with non valid data, the output should be 0.
#     """
#     info("Use flush to remove certain object")
#     client.flush_object(COLLECTION, BUCKET, "post:4")
#
#     info("Use pop to get the object back, and check the existing of this object")
#     assert client.pop(COLLECTION, BUCKET, "post:3", RAND_STRING_3) != 0
#     assert sorted(client.query(COLLECTION, BUCKET, RAND_STRING_3)) == ["post:3"]
#
#     info("Use pop method with non valid data, the output should be 0")
#     assert client.pop(COLLECTION, BUCKET, "post:3", RAND_STRING_1) == 0
#
#
# def test005_flush_collection_and_bucket():
#     """
#     TC 534
#     Test Case to flush for certain collection.
#
#     **Test scenario**
#     #. Push data to sonic server
#     #. Flush certain collection.
#     #. Use count method to check that output, should be 0.
#     """
#
#     info("Flush certain collection")
#     client.flush(COLLECTION)
#
#     info("Use count method to check the length of data after flush, should be 0")
#     assert client.count(COLLECTION, BUCKET) == 0
#
#     info("Use flush to flush non existing collection with certain bucket")
#     client.flush(rand_string(), rand_string())
#
#
# def test006_flush_object_using_collection_bucket():
#     """
#     TC 536
#     Test Case for flush_object method for certain object in certain collection with certain bucket.
#
#     **Test scenario**
#     #. Push data to sonic server
#     #. Use flush_object to flush certain object in collection with certain bucket.
#     #. Use query to check that this record is flushed.
#     """
#     info("Use flush_object to flush certain object in collection with certain bucket")
#     client.flush_object(COLLECTION, BUCKET, "post:4")
#
#     info("Use query to check that this record is flushed")
#     assert client.query(COLLECTION, BUCKET, sub_word) == ["post:5"]
#
#
# def test007_flush_bucket_for_certain_collection():
#     """
#     TC 538
#     Test Case for flush_object method for certain bucket in certain collection.
#
#     **Test scenario**
#     #. Push data to sonic server
#     #. Use flush_bucket method to flush certain bucket.
#     #. Check that there is no more objects in the bucket.
#     """
#
#     info("use flush_bucket method to flush certain bucket")
#     client.flush_bucket(COLLECTION, BUCKET)
#
#     info("Check count in {} bucket, should be 0".format(BUCKET))
#     assert client.count(COLLECTION, BUCKET) == 0
