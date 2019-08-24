from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.types.test(name="duration")' --debug
    """

    return "OK"

    # TODO:*1

    self = j.data.types.get("duration")

    c = """
    1s
    2m
    3h
    4d
    1m2s
    1h2s
    1h2m
    1h2m3s
    1d2s
    1d2m
    1d2m3s
    1d2h
    1d2h3s
    1d2h3m
    1d2h3m4s
    """
    c = j.core.text.strip(c)
    for line in c.split("\n"):
        if line.strip() == "":
            continue
        seconds = self.clean(line)
        out = self.toString(seconds)
        print(out)
        assert line == out

    self.clean("'0'") == 0
    self.clean("'42'") == 42
    self.clean(None) == 0
    self.clean(23) == 23

    self._log_info("TEST DONE DURATION")

    return "OK"
