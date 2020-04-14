from Jumpscale import j


def test015_base():
    """
    to run:

    kosmos 'j.data.types.test(name="int64")'
    """

    t = j.data.types.get("i64")

    assert t.clean("1") == 1
    assert t.clean(1) == 1
    assert t.clean(0) == 0
    assert t.default_get() == 9223372036854775807

    t = j.data.types.get("li64", default="1,2,3")  # list of integers

    assert t._default == [1, 2, 3]

    assert t.default_get() == [1, 2, 3]

    schema_1 = """
        @url = long.test.schema_1
        mylong = 0 (I64)
    """
    s1 = j.data.schema.get_from_text(schema_1)
    obj1 = s1.new()
    obj1.mylong = 9223372036854775807
    obj1.serialize()

    schema_2 = """
            @url = long.test.schema_2
            lmylong = (LI64)
    """
    s2 = j.data.schema.get_from_text(schema_2)
    obj2 = s2.new()
    obj2.lmylong.append(9223372036854775807)
    obj2.lmylong.append(9223372036854775807)
    obj2.serialize()
