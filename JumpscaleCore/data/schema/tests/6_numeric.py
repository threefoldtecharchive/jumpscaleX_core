from Jumpscale import j


def test_numeric():
    """
    to run:

    kosmos 'j.data.schema.test(name="numeric")' --debug
    """
    schema = """
        @url = despiegk.test
        token_price = "10 USD" (N)
        a = "10 USD"
        B = True
        t = (D)
        """

    schema_object = j.data.schema.get_from_text(schema_text=schema)

    assert schema_object.url == "despiegk.test"
    print(schema_object)
    schema_test = schema_object.new()

    schema_test.token_price = "10 USD"

    usd2usd = schema_test.token_price.usd  # convert USD-to-USD... same value
    assert usd2usd == 10
    inr = schema_test.token_price.value_currency("inr")
    # print ("convert 10 USD to INR", inr)
    assert inr > 100  # ok INR is pretty high... check properly in a bit...
    eur = schema_test.token_price.value_currency("eur")
    # print ("convert 10 USD to EUR", eur)
    currency = j.clients.currencylayer
    cureur = currency.cur2usd["eur"]
    curinr = currency.cur2usd["inr"]
    # print (cureur, curinr, o.token_price)
    assert usd2usd * cureur == eur
    assert usd2usd * curinr == inr

    # try EUR to USD as well
    schema_test.token_price = "10 EUR"
    assert schema_test.token_price == b"\x000\n\x00\x00\x00"
    eur2usd = schema_test.token_price.usd
    assert eur2usd * cureur == 10

    schema_test.token_price = "10 EUR"
    assert schema_test.token_price.currency_code == "eur"
    # CLEAN STATE
    # j.data.schema.remove_from_text(schema)
