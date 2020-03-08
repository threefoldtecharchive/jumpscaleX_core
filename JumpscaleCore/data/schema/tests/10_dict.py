from Jumpscale import j


def test_dict():
    """
    to run:

    kosmos 'j.data.schema.test(name="dict")'
    """

    schema0 = """
        @url = despiegk.test.dict
        dd = {} (DICT)
        """

    schema_object = j.data.schema.get_from_text(schema_text=schema0)

    o = schema_object.new()

    o.dd["a"] = 1
    assert o.dd["a"] == 1
    o.dd["b"] = "a"

    assert o.dd == {"a": 1, "b": "a"}

    data = o._data

    o3 = schema_object.new(serializeddata=data)

    assert o3.dd == {"a": 1, "b": "a"}

    j.data.schema._log_info("test for dict ok")

    return "OK"
