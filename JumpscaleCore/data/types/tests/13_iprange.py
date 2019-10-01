from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.types.test(name="iprange")'
    """

    ipv4 = j.data.types.get("iprange", default="192.168.0.0/28")
    assert ipv4.default_get() == "192.168.0.0/28"
    assert ipv4.check("192.168.23.255/28") == True
    assert ipv4.check("192.168.23.300/28") == False
    assert ipv4.check("192.168.23.255/32") == True

    ipv6 = j.data.types.get("iprange")
    assert ipv6.default_get() == "::"
    assert ipv6.check("2001:db00::0/24") == True
    assert ipv6.check("2001:db00::1/24") == True
    assert ipv6.check("2001:db00::0/ffff:ff00::") == False

    self._log_info("TEST DONE LIST")

    return "OK"
