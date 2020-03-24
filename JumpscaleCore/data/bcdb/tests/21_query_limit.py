from Jumpscale import j


def test_main():
    """
    to run:

    kosmos 'j.data.bcdb.test(name="query_limit")'

    """
    schema_text = """
    @url = test.student
    name** = (S)
    age** = (I)
    """
    bcdb, model = j.data.bcdb._test_model_get(schema=schema_text)
    for i in range(100):
        o = model.new()
        o.name = f"student{i}"
        o.age = i % 5
        o.save()

    first_10 = model.find(limit=10)
    assert len(first_10) == 10
    assert first_10[0].name == f"student0"
    assert first_10[9].name == f"student9"

    second_10 = model.find(limit=10, offset=10)
    assert len(second_10) == 10
    assert second_10[0].name == f"student10"
    assert second_10[9].name == f"student19"

    three_years = model.find(age=3)
    assert len(three_years) == 20

    last = model.find(age=3, limit=10, offset=15)
    assert len(last) == 5
    assert last[-1].name == f"student98"
