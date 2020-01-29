from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.schema.test(name="json")'
    """

    schema = """
        @url = despiegk.test.set
        # list_json = (LJSON)
        obj_json = (JSON)  #is same H = SET
        s = "something"
        """

    schema_object = j.data.schema.get_from_text(schema_text=schema)
    assert schema_object.props.obj_json.is_serialized
    # assert schema_object.props.list_json.is_serialized
    assert not schema_object.props.obj_json.is_primitive

    o = schema_object.new()

    o.obj_json["a"] = 1
    o.obj_json["2"] = 1
    assert o.obj_json == {"a": 1, "2": 1}

    serializeddata = o._data

    assert {"obj_json": {"a": 1, "2": 1}, "s": "something"} == o._ddict

    o2 = schema_object.new(serializeddata=serializeddata)

    assert o2.obj_json == {"a": 1, "2": 1}

    self._log_info("test for json ok")

    return "OK"
