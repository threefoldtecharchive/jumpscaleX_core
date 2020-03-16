from Jumpscale import j

skip = j.baseclasses.testtools._skip


def test_redis_index_lost():
    """
    to run:
    kosmos 'j.data.bcdb.test(name="redis_index_lost")'

    """

    SCHEMA = """
    @url = threefoldtoken.wallet.test
    name** = "wallet"
    addr = ""                   # Address
    ipaddr = (ipaddr)           # IP Address
    email = "" (S)              # Email address
    username = "" (S)           # User name

    """

    bcdb = j.data.bcdb.get("test", reset=True)
    m = bcdb.model_get(schema=SCHEMA)
    for i in range(10):
        o = m.new()
        assert o._model.schema.url == "threefoldtoken.wallet.test"
        o.addr = "something:%s" % i
        o.email = "myemail"
        o.name = "myuser_%s" % i
        o.save()

    # we now have some data
    assert len(m.find()) == 10
    r = m.get_by_name("myuser_8")

    assert r.addr == "something:8"

    assert "test" in j.data.bcdb._config

    # j.data.bcdb.bcdb_instances = {}  # make sure we don't have instances in memory

    keylength_before = len(m.find())
    m.index.destroy()
    keylength_after = len(m.find())

    assert keylength_after < keylength_before
    assert len(m.find()) == 0
    bcdb.index_rebuild()
    assert keylength_before == len(m.find())
    # stop redis

    # j.core.redistools.core_stop()
    # assert j.core.redistools.core_running() is False

    # db = j.core.redistools.core_get()
    # assert j.core.redistools.core_running()

    # check the redis is really empty
    # assert j.core.db.keys() == []

    # bcdb = j.data.bcdb.get("test")
    # m = bcdb.model_get(schema=SCHEMA)

    assert len(m.find()) == 10
    r = m.get_by_name("myuser_8")
    assert r.addr == "something:8"

    j.data.bcdb._log_info("TEST DONE")
    return "OK"
