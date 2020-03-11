from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.types.test(name="set")'
    """

    e = j.data.types.get("set")

    assert e.default_get() == (0, 0)
    assert e.clean("1:2") == (1, 2)

    d = 1
    d2 = e.clean(d)
    assert d.to_bytes(8, "little") == e.toBytes(e.clean(d))
    assert d2 == (0, 1)
    assert d == e.toData(d)

    a = b"\x00\x00\x00\x00\xff\xff\xff\xff"
    a2 = e.clean(a)
    assert a == e.toBytes(e.clean(a))
    a2 == "(0, 4294967295)"

    b = b"\xff\xff\xff\xff\xff\xff\xff\xff"
    b2 = e.clean(b)
    assert b == e.toBytes(e.clean(b))
    assert b2 == (4294967295, 4294967295)

    c = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    c2 = e.clean(c)
    assert c == e.toBytes(e.clean(c))
    assert c2 == (0, 0)

    f = 0xFFFFFFFF + 1
    f2 = e.clean(f)
    assert b"\x00\x00\x00\x00\x01\x00\x00\x00" == e.toBytes(e.clean(f))
    assert f2 == (1, 0)
    assert f == e.toData(b"\x00\x00\x00\x00\x01\x00\x00\x00")
    assert f == e.toData(f2)

    return "OK"
