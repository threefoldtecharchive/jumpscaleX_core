from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.types.test(name="numeric")'
    """

    n = j.data.types.numeric

    assert n.NAME == "numeric"

    assert n.bytes2str(n.str2bytes("123456789")) == "123,456,789"
    assert n.bytes2str(n.str2bytes("100000")) == "100,000"
    assert n.bytes2str(n.str2bytes("10000")) == "10,000"
    assert n.bytes2str(n.str2bytes("1000")) == "1,000"
    assert n.bytes2str(n.str2bytes("100")) == "100"

    assert n.bytes2cur(n.str2bytes("10usd"), "eur") < 10
    assert n.bytes2cur(n.str2bytes("10usd"), "eur") > 7
    assert n.bytes2cur(n.str2bytes("10eur"), "eur") == 10
    assert n.bytes2cur(n.str2bytes("10.3eur"), "eur") == 10.3
    assert n.bytes2cur(n.str2bytes("10eur"), "usd") > 10
    assert n.bytes2cur(n.str2bytes("10eur"), "usd") < 15

    assert n.bytes2str(n.str2bytes("10")) == "10"
    assert n.bytes2str(n.str2bytes("10 USD")) == "10"
    assert n.bytes2str(n.str2bytes("10 usd")) == "10"
    assert n.bytes2str(n.str2bytes("10 eur")) == "10 EUR"
    assert n.bytes2str(n.str2bytes("10 keur")) == "10 kEUR"
    assert n.bytes2str(n.str2bytes("10.1 keur")) == "10,100 EUR"
    assert n.bytes2str(n.str2bytes("10,001 eur")) == "10,001 EUR"
    assert n.bytes2str(n.str2bytes("10,001 keur")) == "10,001 kEUR"
    assert n.bytes2str(n.str2bytes("10,001.01 keur")) == "10,001,010 EUR"
    assert n.bytes2str(n.str2bytes("10,001.01 k")) == "10,001,010"
    assert n.bytes2str(n.str2bytes("-10,001.01 k")) == "-10,001,010"
    assert n.bytes2str(n.str2bytes("0.1%")) == "0.1%"
    assert n.bytes2str(n.str2bytes("1%")) == "1%"
    assert n.bytes2str(n.str2bytes("150%")) == "150%"
    assert n.bytes2str(n.str2bytes("-150%")) == "-150%"
    assert n.bytes2str(n.str2bytes("0.001")) == "0.001"
    assert n.bytes2str(n.str2bytes("0.001 eur")) == "0.001 EUR"
    assert n.bytes2str(n.str2bytes("-0.1 eur")) == "-0.1 EUR"

    assert n.bytes2str(n.str2bytes("-0.0001")) == "-0.0001"
    assert n.bytes2cur(n.str2bytes("0.001usd"), "usd") == 0.001
    assert n.bytes2cur(n.str2bytes("0.001k"), "usd") == 1

    # test that encoding currencies that fit in an int are only
    # 6 bytes (1 for type, 1 for currency code, 4 for int)
    # and those that fit into a float are 10 bytes
    # (1 for type, 1 for currency code, 8 for float)
    assert len(n.str2bytes("10 usd")) == 6
    assert len(n.str2bytes("10.0 usd")) == 6
    assert len(n.str2bytes("10.1 usd")) == 10

    cur = n.clean("10k USD")

    assert cur.value == 10000
    assert cur._string == "10 k"

    assert cur._data == b"\n\x97\n\x00\x00\x00"  # binary storage, is what goes to capnp

    cur.value = "11k"
    assert cur.value == 11000  # default is USD

    cur.value = "1"
    assert cur.value == 1

    res = cur + 2

    assert res.value == 3

    res = cur + cur

    assert res.value == 2

    res = cur * cur
    assert res.value == 1

    res = n.clean("10k") * 2
    assert res.value == 20000

    self._log_info("TEST NUMERIC DONE")

    return "OK"
