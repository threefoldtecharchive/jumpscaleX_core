from Jumpscale import j


def test013_ip_range():
    """
    to run:

    kosmos 'j.data.types.test(name="iprange")'
    """

    ipv4 = j.data.types.get("iprange", default="192.168.0.0/28")
    assert ipv4.default_get() == "192.168.0.0/28"
    assert ipv4.check("192.168.23.255/28") is True
    assert ipv4.check("192.168.23.300/28") is False
    assert ipv4.check("192.168.23.255/32") is True

    ipv6 = j.data.types.get("iprange")
    assert ipv6.default_get() == "::/128"
    assert ipv6.check("2001:db00::0/24") is True
    assert ipv6.check("2001:db00::1/24") is True
    assert ipv6.check("2001:db00::0/ffff:ff00::") is False

    j.data.types._log_info("TEST DONE LIST")

    return "OK"
