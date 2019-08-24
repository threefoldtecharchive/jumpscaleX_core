from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.types.test(name="datetime")'
    """

    tt = j.data.types.datetime

    c = """
    11/30 22:50
    11/30
    1990/11/30
    1990/11/30 10am:50
    1990/11/30 10pm:50
    1990/11/30 22:50
    30/11/1990
    30/11/1990 10pm:50
    """
    c = j.core.text.strip(c)
    out = ""
    for line in c.split("\n"):
        if line.strip() == "":
            continue
        epoch = tt.clean(line)
        out += "%s -> %s\n" % (line, tt.toString(epoch))
    out_compare = """
    11/30 22:50 -> 2019/11/30 22:50:00
    11/30 -> 2019/11/30 00:00:00
    1990/11/30 -> 1990/11/30 00:00:00
    1990/11/30 10am:50 -> 1990/11/30 10:50:00
    1990/11/30 10pm:50 -> 1990/11/30 22:50:00
    1990/11/30 22:50 -> 1990/11/30 22:50:00
    30/11/1990 -> 1990/11/30 00:00:00
    30/11/1990 10pm:50 -> 1990/11/30 22:50:00
    """
    print(out)
    out = j.core.text.strip(out)
    out_compare = j.core.text.strip(out_compare)
    assert out == out_compare

    assert tt.clean(0) == 0

    tt.clean("-0s") == j.data.time.epoch

    tt.clean("'0'") == 0

    print("test j.data.types.date.datetime() ok")

    tt = j.data.types.date

    c = """
    11/30
    1990/11/30
    30/11/1990
    """
    c = j.core.text.strip(c)
    out = ""
    for line in c.split("\n"):
        if line.strip() == "":
            continue
        epoch = tt.clean(line)
        out += "%s -> %s\n" % (line, tt.toString(epoch))
    out_compare = """
    11/30 -> 2019/11/30
    1990/11/30 -> 1990/11/30
    30/11/1990 -> 1990/11/30
    """
    print(out)
    out = j.core.text.strip(out)
    out_compare = j.core.text.strip(out_compare)
    assert out == out_compare

    assert tt.clean(0) == 0
    assert tt.clean("") == 0

    tt.clean("-0s") == j.data.time.epoch

    print("test j.data.types.date.test() ok")

    # tt._log_info("TEST DONE")

    return "OK"
