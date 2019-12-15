from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.bcdb.test(name="schema_update")'


    """

    bcdb, _ = self._load_test_model()

    schema_1 = """
    @url = jumpscale.bcdb.test.house
    name** = "" (S)
    active** = "" (B)
    enum = "a,b,c" (E)
    cost** =  (N)

    @url = jumpscale.bcdb.test.room1
    name** = "" (S)
    """

    model = bcdb.model_get(schema=schema_1)
    schema_md5 = model.schema._md5

    model_obj = model.new()
    model_obj.name = "one"
    model_obj.active = True
    model_obj.cost = "10 USD"
    model_obj.save()

    exception = False
    try:
        model_obj.newprop
    except:
        exception = True

    assert exception

    data = model.get(model_obj.id)

    # make sure the data from first one has right schema md5
    assert data._schema._md5 == schema_md5
    assert data.cost_usd == 10
    assert model_obj.cost_usd == 10

    schema_2 = """
    @url = jumpscale.bcdb.test.house
    name** = "" (S)
    active** = "" (B)
    cost** =  (N)
    enum = "a,b,c,d" (E)
    newprop = ""
    room = (LO) !jumpscale.bcdb.test.room1
    """

    model_updated = bcdb.model_get(schema=schema_2)

    data = model_updated.get(model_obj.id)
    data.enum = "d"
    assert data.newprop == ""
    assert data.room == []

    model = bcdb.model_get(url="jumpscale.bcdb.test.house")
    assert model.schema._md5 == model_updated.schema._md5

    return "OK"
