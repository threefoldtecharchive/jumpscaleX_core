from Jumpscale import j


def test001_base():
    """
    to run:

    kosmos 'j.data.types.test(name="base")'
    """

    assert j.data.types.string.__class__.NAME == "string"

    assert j.data.types.get("s") == j.data.types.get("string")
    assert j.data.types.get("s") == j.data.types.get("str")

    t = j.data.types.get("i")

    assert t.clean("1") == 1
    assert t.clean(1) == 1
    assert t.clean(0) == 0
    assert t.default_get() == 2147483647

    t = j.data.types.get("li", default="1,2,3")  # list of integers

    assert t._default == [1, 2, 3]

    assert t.default_get() == [1, 2, 3]

    t2 = j.data.types.get("ls", default="1,2,3")  # list of strings
    assert t2.default_get() == ["1", "2", "3"]

    t3 = j.data.types.get("ls")
    assert t3.default_get() == []

    t = j.data.types.email
    assert t.check("kristof@in.com")
    assert t.check("kristof.in.com") is False

    t = j.data.types.bool
    assert t.clean("true") is True
    assert t.clean("True") is True
    assert t.clean(1) is True
    assert t.clean("1") is True
    assert t.clean("False") is False
    assert t.clean("false") is False
    assert t.clean("0") is False
    assert t.clean(0) is False
    assert t.check(1) is False
    assert t.check(True) is True

    b = j.data.types.get("b", default="true")

    assert b.default_get() is True

    # TODO: need more tests here

    j.data.types._log_info("TEST DONE FOR TYPES BASE")

    return "OK"
