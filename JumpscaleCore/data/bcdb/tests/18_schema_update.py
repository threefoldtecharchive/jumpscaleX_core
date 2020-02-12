from Jumpscale import j


def test_schema_update():
    """
    to run:

    kosmos 'j.data.bcdb.test(name="schema_update")'

    This test tests bcdb schema's autoupgrade. When you add/remove fields to a schema, bcdb will
    automatically use the latest schema, as long as the changes don't include indexed fields
    """

    bcdb, _ = j.data.bcdb._load_test_model()

    # to cover all cases, we'll test adding/removing fields of simeple types, and also type object. Also, test that a sub object's fields change

    old_schema = """
    @url = jumpscale.bcdb.test.house
    name** = "" (S)
    active** = "" (B)
    enum = "a,b,c" (E) # enum field that will be modified
    cost** =  (N)
    toremove = "" # field to be removed
    furniture = (O) !jumpscale.bcdb.test.furniture
    owner = (O) !jumpscale.bcdb.test.owner

    @url = jumpscale.bcdb.test.room
    name = "" (S)

    @url = jumpscale.bcdb.test.furniture
    name = "" (S)

    @url = jumpscale.bcdb.test.owner
    name = "" (S)
    """

    model = bcdb.model_get(schema=old_schema)
    schema_md5 = model.schema._md5

    obj = model.new()
    obj.name = "one"
    obj.active = True
    obj.cost = "10 USD"
    obj.furniture.name = "chair"
    obj.owner.name = "kristof"
    obj.save()

    # make sure fields that will be added to the changed schema aren't there
    assert not hasattr(obj, "newprop")
    assert not hasattr(obj, "room")
    assert not hasattr(obj.owner, "email")

    # make sure fields that will be removed from the changed schena aren't there
    assert hasattr(obj, "toremove")

    obj = model.get(obj.id)

    # make sure the data from first obj has right schema md5
    assert obj._schema._md5 == schema_md5

    schema_2 = """
    @url = jumpscale.bcdb.test.house
    name** = "" (S)
    active** = "" (B)
    cost** =  (N)
    enum = "a,b,c,d" (E) # enum field that was modified
    newprop = "" # new field added
    room = (O) !jumpscale.bcdb.test.room
    owner = (O) !jumpscale.bcdb.test.owner

    @url = jumpscale.bcdb.test.owner
    name = "" (S)
    email = "" (S)
    """

    model_updated = bcdb.model_get(schema=schema_2)

    obj = model_updated.get(obj.id)
    obj.enum = "d"

    # make sure that new fields are there
    assert hasattr(obj, "newprop")
    assert hasattr(obj, "room")
    # assert hasattr(obj.owner, "email") # @todo implement auto update to sub objects too

    # make sure that removed fields aren't there
    assert not hasattr(obj, "toremove")
    assert not hasattr(obj, "furniture")

    # get the model again using the url to make sure it will get the latest
    model = bcdb.model_get(url="jumpscale.bcdb.test.house")
    assert model.schema._md5 == model_updated.schema._md5

    obj = model.new()
    assert hasattr(obj, "newprop")
    assert hasattr(obj, "room")

    # assert hasattr(obj.owner, "email") # @todo implement auto update to sub objects too

    assert not hasattr(obj, "toremove")
    assert not hasattr(obj, "furniture")

    obj.name = "two"
    obj.active = True
    obj.cost = "10 USD"
    obj.room = {"name": "kitchen"}
    obj.save()

    return "OK"
