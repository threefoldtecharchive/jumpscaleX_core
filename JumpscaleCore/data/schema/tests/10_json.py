from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.schema.test(name="json")' --debug
    """

    schema = """
        @url = despiegk.test.set
        list_json = (LJSON)
        obj_json = (JSON)  #is same H = SET
        s = "something"
        """

    schema_object = j.data.schema.get_from_text(schema_text=schema)

    o = schema_object.new()

    o.obj_json["a"] = 1
    o.obj_json["2"] = 1
    assert o.obj_json == {"a": 1, "2": 1}

    serializeddata = o._data

    o2 = schema_object.new(serializeddata=serializeddata)

    assert o2.obj_json == {"a": 1, "2": 1}

    self._log_info("test for json ok")

    return "OK"
