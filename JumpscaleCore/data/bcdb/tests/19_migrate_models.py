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

    kosmos 'j.data.bcdb.test(name="migrate_models")'
    """

    bcdb, _ = self._load_test_model()

    schema_1 = """
    @url = jumpscale.bcdb.test.house.1
    name** = "" (S)
    active** = "" (B)
    enum = "a,b,c" (E)
    cost** =  (N)
    notindexed = "" (S)
    todelete = "" (S)
    """

    model = bcdb.model_get(schema=schema_1)
    schema_md5 = model.schema._md5

    obj = model.new()
    obj.name = "one"
    obj.active = True
    obj.cost = "10 USD"
    obj.save()

    assert len(model.find()) == 1
    assert obj.notindexed == ""
    assert obj.todelete == ""

    schema_2 = """
    @url = jumpscale.bcdb.test.house.2
    name** = "" (S)
    active** = "" (B)
    cost** =  (N)
    notindexed** = "" (S)
    newindexed** = "" (S)
    newenum** = "e,f,g" (E)
    enum = "a,b,c,d" (E)
    newprop = ""
    """
    new_model = bcdb.model_get(schema=schema_2)

    bcdb.migrate_models(model.schema.url, new_model.schema.url)
    assert len(model.find()) == 0

    objs = new_model.find()
    assert len(objs) == 1

    obj = objs[0]
    assert obj.notindexed != ""
    assert obj.newindexed != ""
    assert obj.newenum == "E"
    assert obj.newprop == ""
    assert not hasattr(obj, "todelete")

    return "OK"
