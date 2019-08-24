# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


from Jumpscale import j


def main(self):
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
