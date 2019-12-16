from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.schema.test(name="set")' --debug
    """

    schema = """
        @url = despiegk.test.set
        llist = (LSET)
        llist2 = (LH)  #is same H = SET
        hash = (SET)
        """

    schema_object = j.data.schema.get_from_text(schema_text=schema)

    assert schema_object.url == "despiegk.test.set"
    print(schema_object)

    o = schema_object.new()

    assert o.hash == (0, 0)
    assert o.llist == []

    o.hash = 1
    assert o.hash == (0, 1)

    o.hash = "0:1"
    assert o.hash == (0, 1)

    o.hash = "1:2"
    assert o.hash == (1, 2)

    o.llist.append("1:2")
    o.llist.append("2:3")

    assert ["1:2", "2:3"] == o.llist

    o.llist = [1, 2]
    assert o.llist == [1, 2]

    d = [(0, x) for x in range(10)]
    o.llist2 = d
    assert o.llist2 == d
    # CLEAN STATE
    # j.data.schema.remove_from_text(schema)
    return "OK"
