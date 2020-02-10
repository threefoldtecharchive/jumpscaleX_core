from Jumpscale import j


def test_models():
    """
    to run:

    kosmos 'j.data.bcdb.test(name="models")'

    work with toml files and see if models get generated properly

    """

    mpath = j.data.bcdb._dirpath + "/tests/models"
    assert j.sal.fs.exists(mpath)

    # make sure we remove the maybe already previously generated model file
    for item in j.sal.fs.listFilesInDir(mpath, filter="*.py"):
        j.sal.fs.remove(item)

    bcdb, _ = j.data.bcdb._load_test_model()

    assert bcdb.name in j.data.bcdb.instances

    bcdb.models_add(mpath)

    s = """
@url = jumpscale.bcdb.test.house
0 : name** = "" (S)
1 : active** = "" (B)
2 : cost** =  (N)
3 : room = (LO) !jumpscale.bcdb.test.room

""".lstrip()

    # check the right schema in meta stor
    s_ = j.data.schema.get(url="jumpscale.bcdb.test.house")
    assert j.data.schema._md5(s) == s_._md5

    model = bcdb.model_get(url="jumpscale.bcdb.test.house")
    assert model.schema._md5 == j.data.schema._md5(s)

    schema_md5 = model.schema._md5

    model_obj = model.new()
    model_obj.cost = "10 USD"
    model_obj.name = "House"

    model_obj.save()
    assert model_obj.id

    data = model.get(model_obj.id)

    # make sure the data from first one has right schema md5
    assert data._schema._md5 == schema_md5

    assert data.cost_usd == 10

    assert model_obj.cost_usd == 10

    schema_updated = """@url = jumpscale.bcdb.test.house
    0 : name** = "" (S)
    1: active** = "" (B)
    2 : cost** = (N)
    3 : room = (LS)
"""
    ms = model.find()
    assert len(ms) == 1
    md5 = ms[0]._schema._md5

    model_updated = bcdb.model_get(schema=schema_updated)

    s_ = j.data.schema.get(url="jumpscale.bcdb.test.house")
    assert j.data.schema._md5(schema_updated) == s_._md5

    ms = model.find()
    assert len(ms) == 1

    # schema updated so md5 not equal to old one
    assert ms[0]._schema._md5 != md5

    # Update schema

    s_updated = model_updated.schema
    assert s_updated._md5 != schema_md5

    model2 = bcdb.model_get(url="jumpscale.bcdb.test.house")

    assert model2.schema._md5 == s_updated._md5

    assert len(model2.find()) == 1

    model_obj = model_updated.new()
    model_obj.cost = 15
    model_obj.name = "test_name_because_there_is_a_unique_constraint_on_it"
    model_obj.save()

    assert len(model_updated.find()) == 2

    obj = model_updated.find()[1]

    assert obj._schema._md5 == s_updated._md5  # needs to be the new md5

    model.find()[0].cost == "10 USD"
    model.find()[1].cost == 15
    print(model.find()[1])

    # the schema's need to be different

    res = model.find()
    # Auto migration!
    assert res[0]._schema._md5 == res[1]._schema._md5

    # CLEAN STATE
    j.servers.zdb.test_instance_stop()
    j.servers.sonic.default.stop()
    return "OK"
