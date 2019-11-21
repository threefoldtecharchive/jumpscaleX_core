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

    kosmos 'j.data.bcdb.test(name="schema_update")'


    """

    bcdb, _ = self._load_test_model()

    schema_1 = """
    @url = jumpscale.bcdb.test.house
    name** = "" (S)
    active** = "" (B)
    enum = "a,b,c" (E)
    cost** =  (N)

    @url = jumpscale.bcdb.test.room1
    name** = "" (S)
    """

    model = bcdb.model_get(schema=schema_1)
    schema_md5 = model.schema._md5

    model_obj = model.new()
    model_obj.cost = "10 USD"
    model_obj.save()

    exception = False
    try:
        model_obj.newprop = "a"
    except:
        exception = True
    # assert exception  #TODO: needs to be re-enabled

    data = model.get(model_obj.id)

    oldid = model_obj.id + 0  # to have copy for sure

    # make sure the data from first one has right schema md5
    assert data._schema._md5 == schema_md5
    assert data.cost_usd == 10
    assert model_obj.cost_usd == 10

    schema_2 = """
    @url = jumpscale.bcdb.test.house
    name** = "" (S)
    active** = "" (B)
    cost** =  (N)
    enum = "a,b,c,d" (E)
    newprop = ""
    room = (LO) !jumpscale.bcdb.test.room1
    """

    model_updated = bcdb.model_get(schema=schema_2)

    data = model_updated.get(oldid)
    data.enum = "d"
    data.newprop = "a"
    assert data.newprop == "a"

    return "OK"
