from Jumpscale import j


def test():
    """
    to run:

    kosmos 'j.clients.logger.test(name="base")'
    """
    self = j.clients.logger
    if j.application.appname != "test":
        j.application.start("test")

    cl = self.get(name="main")
    cl.delete_all()

    for i in range(2100 + 1):
        j.core.tools.log(msg="logs:%s" % i, cat=None, level=10, data=None, context=None, replace=True)

    def do(logdict, args):
        args["counter"] += 1
        args["ids"].append(logdict["id"])

    fromtime = j.data.types.datetime.clean("-1h")
    res = cl._data_container_ids_get_from_time(epoch_from=fromtime, appname="test")
    assert res == [1]

    args = {}
    args["counter"] = 0
    args["ids"] = []
    args = cl.walk(do, time_from="-1h", maxitems=100, appname="test", args=args)
    assert len(args["ids"]) == 100
    assert args["counter"] == 100
    assert args["ids"][0] == 1
    assert args["ids"][99] == 100
    assert args["ids"][-1] == 100

    args = {}
    args["counter"] = 0
    args["ids"] = []
    args = cl.walk(do, time_from="-1h", appname="test", args=args)
    assert len(args["ids"]) == 2100
    assert args["counter"] == 2100
    assert args["ids"][0] == 1
    assert args["ids"][2099] == 2100
    assert args["ids"][-1] == 2100

    args = {}
    args["counter"] = 0
    args["ids"] = []
    args, lastid = cl.walk_reverse(do, time_from="-1h", appname="test", args=args, maxitems=10)

    assert len(args["ids"]) == 10
    assert args["counter"] == 10
    assert args["ids"] == [2092, 2093, 2094, 2095, 2096, 2097, 2098, 2099, 2100, 2101]

    # will get the latest 10 logs
    res, lastid = cl.tail_get(appname="test", maxitems=10)
    assert len(res) == 10
    assert lastid == 2101

    for i in range(3000, 3020):
        j.core.tools.log(msg="logs:%s" % i, cat=None, level=10, data=None, context=None, replace=True)

    res, lastid = cl.tail_get(appname="test", lastid=lastid)
    res2 = [i["id"] for i in res]

    assert len(res2) == 20
    assert [
        2102,
        2103,
        2104,
        2105,
        2106,
        2107,
        2108,
        2109,
        2110,
        2111,
        2112,
        2113,
        2114,
        2115,
        2116,
        2117,
        2118,
        2119,
        2120,
        2121,
    ] == res2

    for i in range(4000, 4010):
        j.core.tools.log(msg="logs:%s" % i, cat=None, level=10, data=None, context=None, replace=True)
    res, lastid = cl.tail_get(appname="test", lastid=lastid)
    res2 = [i["id"] for i in res]
    assert len(res2) == 10

    assert res[-1]["message"] == "logs:4009"

    for i in range(5000, 5010):
        j.core.tools.log(msg="logs:%s" % i, cat=None, level=10, data=None, context=None, replace=True)

    # FOR INTERACTIVE
    # print("lastid:%s" % lastid)
    # cl.tail(appname="test", lastid=lastid)

    res = cl.tail(appname="test", lastid=lastid, wait=False)
    assert len(res) == 10

    for i in range(2000 + 1):
        j.core.tools.log(msg="logs2:%s" % i, cat=None, level=10, data=None, context=None, replace=True)

    logging_dir = j.sal.fs.joinPaths(cl._log_dir, "test")
    assert len(j.sal.fs.listFilesInDir(logging_dir)) == 3

    assert cl.count("test") == 1142
    assert cl.count("test", all=True) == 4142

    for i in range(6000, 6010):
        j.core.tools.log(msg="logs2:%s" % i, cat=None, level=10, data=None, context=None, replace=True)

    assert cl.count("test") == 1142 + 10
    assert cl.count("test", all=True) == 4142 + 10

    for i in range(6020, 6030):
        j.core.tools.log(msg="testfind:%s" % i, cat=None, level=20, data=None, context=None, replace=True)

    for i in range(6030, 6035):
        j.core.tools.log(msg="testcount:%s" % i, cat=None, level=30, data=None, context=None, replace=True)

    # tests for find & filters
    assert len(cl.find(message="testfind")) == 10
    assert len(cl.find(message="testfind", level=20)) == 10
    assert len(cl.find(message="testcount", level=30)) == 5
    for i in range(6030, 6032):
        j.core.tools.log(msg="testcount:%s" % i, cat="test_cat", level=30, data="some data", context=None, replace=True)

    assert len(cl.find(message="testcount", level=30, cat="test_cat", data="some data")) == 2

    print("OK")
