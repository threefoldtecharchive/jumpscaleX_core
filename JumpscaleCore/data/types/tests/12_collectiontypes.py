from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.types.test(name="collectiontypes")'
    """

    e = j.data.types.get("json")

    ddict = {}
    ddict["a"] = 1
    ddict["b"] = "b"

    ddict2 = e.clean(ddict)
    assert {"a": 1, "b": "b"} == ddict2

    assert j.data.types.dict.check(ddict2)

    data = e.toData(ddict2)

    assert {"a": 1, "b": "b"} == e.clean(data)

    # assert e.toString(data) == "{'a': 1, 'b': 'b'}"
    #
    # datastr = e.toString(data)
    #
    # assert datastr == "{'a': 1, 'b': 'b'}"

    return "OK"
