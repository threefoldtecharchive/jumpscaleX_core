from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.types.test(name="enumeration")'
    """

    e = j.data.types.get("e", default="yellow,blue,red")

    assert str(e) == "ENUM: YELLOW,BLUE,RED (default:YELLOW)"

    assert e.toString(2) == "BLUE"
    assert e.toString(3) == "RED"

    try:
        e.clean(4)
        raise j.exceptions.Value("should not work")
    except Exception:
        pass

    str(e.clean(0)) == "UNKNOWN"

    assert e.toString(" blue") == "BLUE"
    assert e.toString("Red ") == "RED"

    assert str(e.clean("Red ")) == "RED"
    assert str(e.clean("BLUE ")) == "BLUE"
    assert str(e.clean("YELLOW ")) == "YELLOW"

    # start count from 1 (0 is for None)
    assert e.toData("BLUE ") == 2
    assert e.toData("Red ") == 3
    assert e.toData("YELLOW ") == 1

    assert e._jsx_location == "j.data.types._types['enum_b3fb5d69cff844ccc156a430ea82e83b']"
    e = j.data.types._types["enum_b3fb5d69cff844ccc156a430ea82e83b"]
    assert str(e) == "ENUM: YELLOW,BLUE,RED (default:YELLOW)"

    enum = e.clean(1)
    enum2 = e.clean(2)
    enum3 = e.clean(1)

    assert enum.value == 1

    assert enum == enum3
    assert enum != enum2

    assert e.RED == e.clean(3)
    assert e.RED == "RED"

    assert str(enum3) == "YELLOW"
    assert enum3.BLUE == enum2.BLUE
    assert str(enum3) == "BLUE"

    self._log_info("TEST DONE ENUMERATION")

    return "OK"
