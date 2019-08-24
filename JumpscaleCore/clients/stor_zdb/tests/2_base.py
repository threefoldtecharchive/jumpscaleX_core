from Jumpscale import j
import os


def main(self):
    """
    to run:
    
    kosmos 'j.clients.zdb._test_run(name="base")'

    """

    c = self.client_admin_get(port=9901)
    c.namespace_new("test", secret="1234")

    cl = self.client_get(name="test", addr="localhost", port=9901, secret="1234")
    cl.flush()
    nr = cl.nsinfo["entries"]
    assert nr == 0

    id = cl.set(b"INIT")
    assert id == 0
    assert cl.get(0) == b"INIT"

    nr = cl.nsinfo["entries"]
    assert nr == 1
    # do test to see that we can compare
    id = cl.set(b"r")
    assert id == 1
    assert cl.get(id) == b"r"

    id2 = cl.set(b"b")
    assert id2 == 2

    assert cl.set(b"r", key=id) is None
    assert cl.set(b"rss", key=id) == 1  # changed the data, returns id 1

    nr = cl.nsinfo["entries"]
    assert nr == 3  # nr of real data inside

    # test the list function
    assert cl.list() == [0, 1, 2]
    assert cl.list(2) == [2]
    assert cl.list(0) == [0, 1, 2]

    result = {}
    for id, data in cl.iterate():
        if id == 0:
            continue
        self._log_debug("%s:%s" % (id, data))
        result[id] = data

    assert {1: b"rss", 2: b"b"} == result

    assert cl.list(key_start=id2)[0] == id2

    assert cl.exists(id2)

    self._log_debug("write 10000 entries")

    def dumpdata(self):

        inputs = {}
        for i in range(1000):
            data = os.urandom(4096)
            key = cl.set(data)
            inputs[key] = data

        for k, expected in inputs.items():
            actual = cl.get(k)
            if expected != actual:
                j.shell()
            assert expected == actual

    dumpdata(self)  # is in default namespace

    self._log_debug("count:%s" % cl.count)

    nsname = "newnamespace"

    c = self.client_admin_get(name="admin", port=9901)

    c.namespace_new(nsname, secret="1234", maxsize=1000)

    ns = self.get(name=nsname, nsname=nsname, secret_="1234", port=9901)
    ns.flush()

    assert ns.nsinfo["data_limits_bytes"] == 1000
    assert ns.nsinfo["data_size_bytes"] == 0
    assert ns.nsinfo["data_size_mb"] == 0.0
    assert int(ns.nsinfo["entries"]) == 0
    assert ns.nsinfo["index_size_bytes"] == 0
    assert ns.nsinfo["index_size_kb"] == 0.0
    assert ns.nsinfo["name"] == nsname
    assert ns.nsinfo["password"] == "yes"
    assert ns.nsinfo["public"] == "no"

    assert ns.nsname == nsname

    # both should be same
    id = ns.set(b"a")
    assert ns.get(id) == b"a"
    assert ns.nsinfo["entries"] == 1

    try:
        dumpdata(ns)
    except Exception as e:
        assert "No space left" in str(e)

    c.namespace_new(nsname + "2", secret="1234")

    nritems = 1000
    j.tools.timer.start("zdb")

    self._log_debug("perftest for 10.000 records, should get above 5k per sec, +10k expected")
    for i in range(nritems):
        id = cl.set(b"a")

    res = j.tools.timer.stop(nritems)

    assert res > 3000

    self._log_info("PERF TEST SEQ OK")
    return "OK"
