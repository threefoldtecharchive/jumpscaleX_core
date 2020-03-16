from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.types.test(name="list")'
    """

    tt = j.data.types.get("l", default="1,2,3")  # should return list of strings

    C = """
    - 1
    - 2
    - 3
    """
    C = j.core.text.strip(C).strip()
    str(tt.default_get()).strip() == C

    l = tt.clean(val="3,4,5")

    assert l[1] == "4"
    # l is now a list of strings

    tt = j.data.types.get("li", default="1,2,3")  # should be a list of integers
    l = tt.clean(val="3,4,5")

    assert l[1] == 4

    assert 4 in l
    assert not "4" in l

    l = tt.default_get()
    C = """
    - 1
    - 2
    - 3
    """
    C = j.core.text.strip(C).strip()
    assert str(l).strip() == C
    l = tt.clean(l[:])  # avoid manipulating list factory default
    l.append(4)
    l.append("5")

    assert l == [1, 2, 3, 4, 5]
    assert len(l) == 5

    assert 5 in l

    l[1] = 10
    assert l == [1, 10, 3, 4, 5]
    assert len(l) == 5

    self._log_info("TEST DONE LIST")

    return "OK"
