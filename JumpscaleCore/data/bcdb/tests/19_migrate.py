from Jumpscale import j


def test_migrate_models():
    """
    to run:

    kosmos 'j.data.bcdb.test(name="migrate")'
    """

    bcdb, _ = j.data.bcdb._test_model_get()

    schema_1 = """
    @url = jumpscale.bcdb.test.house.1
    name** = "" (S)
    active** = "" (B)
    enum = "a,b,c" (E)
    cost** =  (N)
    notindexed = "" (S)
    todelete = "" (S)
    """

    model = bcdb.model_get(schema=schema_1)
    schema_md5 = model.schema._md5

    obj = model.new()
    obj.name = "one"
    obj.active = True
    obj.cost = "10 USD"
    obj.save()

    assert len(model.find()) == 1
    assert obj.notindexed == ""
    assert obj.todelete == ""

    schema_2 = """
    @url = jumpscale.bcdb.test.house.2
    name** = "" (S)
    active** = "" (B)
    cost** =  (N)
    notindexed** = "" (S)
    newindexed** = "" (S)
    newenum** = "e,f,g" (E)
    enum = "a,b,c,d" (E)
    newprop = ""
    """
    new_model = bcdb.model_get(schema=schema_2)

    bcdb.migrate_models(model.schema.url, new_model.schema.url)
    assert len(model.find()) == 0

    objs = new_model.find()
    assert len(objs) == 1

    obj = objs[0]
    assert obj.notindexed != ""
    assert obj.newindexed != ""
    assert obj.newenum == "E"
    assert obj.newprop == ""
    assert not hasattr(obj, "todelete")

    return "OK"
