from Jumpscale import j


def test_async():
    """
    to run:

    kosmos 'j.data.bcdb.test(name="async")'

    this is a test where we use the queuing mechanism for processing data changes

    """

    _, model = j.data.bcdb._test_model_get()

    def get_obj(i):
        model_obj = model.new()
        model_obj.nr = i
        model_obj.name = "somename%s" % i
        return model_obj

    model_obj = get_obj(1)

    # should be empty
    assert model.bcdb.queue.empty() is True

    model.set_dynamic(model_obj)
    model_obj2 = model.get(model_obj.id)
    assert model_obj2._ddict_hr == model_obj._ddict_hr

    # will process 1000 obj (set)
    for x in range(2, 100):
        model.set_dynamic(get_obj(x))

    # should be nothing in queue
    assert model.bcdb.queue.empty() is True

    # now make sure index processed and do a new get
    model.index_ready()

    model_obj2 = model.get(model_obj.id)
    assert model_obj2._ddict_hr == model_obj._ddict_hr

    assert model.bcdb.queue.empty()

    j.data.bcdb._log_info("TEST ASYNC DONE")

    return "OK"


# Teardown
def after():
    # Destroy zdb databases
    j.data.bcdb.test_zdb.destroy()
    # Stop and delete sonic
    j.servers.sonic.testserver.stop()
    j.servers.sonic.testserver.delete()
    # Stop and delete zdb
    j.servers.zdb.testserver.stop()
    j.servers.zdb.testserver.delete()

