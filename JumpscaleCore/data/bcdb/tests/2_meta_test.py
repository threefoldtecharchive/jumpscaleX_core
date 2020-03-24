from Jumpscale import j




def test_meta():
    """
    to run:

    kosmos 'j.data.bcdb.test(name="meta_test")'

    """

    bcdb, _ = j.data.bcdb._test_model_get()

    assert len(bcdb.get_all()) == 0

    s = list(j.data.schema.schemas_loaded.keys())

    assert "despiegk.test" in s

    m = bcdb.model_get(url="despiegk.test")

    schema_text = """
    @url = jumpscale.schema.test.a
    category**= ""
    txt = ""
    i = 0
    """
    s = bcdb.schema_get(schema=schema_text)

    assert s.properties_unique == []

    assert "jumpscale.schema.test.a" in j.data.schema.schemas_loaded
    assert "jumpscale.bcdb.circle.2" in j.data.schema.schemas_loaded

    schema = bcdb.model_get(url="jumpscale.schema.test.a")
    o = schema.new()

    assert "jumpscale.schema.test.a" in j.data.schema.schemas_loaded
    assert "jumpscale.bcdb.circle.2" in j.data.schema.schemas_loaded

    s0 = bcdb.schema_get(url="jumpscale.schema.test.a")
    s0md5 = s0._md5 + ""

    model = bcdb.model_get(schema=s0)

    assert bcdb.get_all() == []  # just to make sure its empty

    # @TODO: get accurate number since this keep changes
    # assert len(j.data.schema.meta._data["url"]) == 7

    a = model.new()
    a.category = "acat"
    a.txt = "data1"
    a.i = 1
    a.save()

    a2 = model.new()
    a2.category = "acat2"
    a2.txt = "data2"
    a2.i = 2
    a2.save()

    assert len([i for i in model.index.model.find()]) == 2

    myid = a.id + 0

    assert a._model.schema._md5 == s0md5

    # lets upgrade schema to float
    s_temp = bcdb.schema_get(schema=schema_text)

    assert s_temp._md5 == s0._md5

    # lets upgrade schema to float
    s2 = bcdb.schema_get(schema=schema_text)

    model2 = bcdb.model_get(schema=s2)

    a3 = model2.new()
    a3.category = "acat3"
    a3.txt = "data3"
    a3.i = 3
    a3.save()
    assert a3.i == 3.0
    assert a2.i == 2  # int

    assert len(model2.find()) == 3  # needs to be 3 because model is for all of them
    assert len(model.find()) == 3  # needs to be 3 because model is for all of them

    all = model2.find()
    print(all)
    a4 = model2.get(all[0].id)
    a4_ = model.get(all[0].id)
    assert a4_ == a4
    a5 = model2.get(all[1].id)
    a6 = model.get(all[2].id)
    a6_ = model.get(all[2].id)
    assert a6_ == a6

    assert a6.id == a3.id
    assert a6.i == a3.i

    j.data.bcdb._log_info("TEST META DONE")

    return "OK"
