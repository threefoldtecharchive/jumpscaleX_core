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

    kosmos 'j.data.bcdb.test(name="models")'

    work with toml files and see if models get generated properly

    """
    mpath = self._dirpath + "/tests/models"
    assert j.sal.fs.exists(mpath)

    # make sure we remove the maybe already previously generated model file
    for item in j.sal.fs.listFilesInDir(mpath, filter="*.py"):
        j.sal.fs.remove(item)

    bcdb, _ = self._load_test_model()

    assert bcdb in j.data.bcdb.instances

    bcdb.models_add(mpath)

    model = bcdb.model_get(url="jumpscale.bcdb.test.house")

    schema_md5 = model.schema._md5

    model_obj = model.new()
    model_obj.cost = "10 USD"
    model_obj.save()

    data = model.get(model_obj.id)

    # make sure the data from first one has right schema md5
    assert data._schema._md5 == schema_md5

    assert data.cost_usd == 10

    assert model_obj.cost_usd == 10

    schema_updated = """
    @url = jumpscale.bcdb.test.house
    name* = "" (S)
    active* = "" (B)
    cost* = (N)
    newprop = ""
    room = (LO) !jumpscale.bcdb.test.room
    """

    assert len(model.find()) == 1

    model = bcdb.model_get(schema=schema_updated)
    s = model.schema
    assert s._md5 != schema_md5

    model2 = bcdb.model_get(url="jumpscale.bcdb.test.house")

    assert model2.schema._md5 == s._md5

    assert model2 == model

    assert len(model2.find()) == 1

    model_obj = model.new()
    model_obj.cost = 15
    model_obj.save()

    assert len(model2.find()) == 2
    assert len(model.find()) == 2

    data2 = model.find()[1]
    assert data2._schema._md5 == s._md5  # needs to be the new md5

    model.find()[0].cost == "10 USD"
    model.find()[1].cost == 15
    print(model.find()[1])
    # the schema's need to be different
    assert model.find()[0]._schema._md5 != model.find()[1]._schema._md5

    return "OK"
