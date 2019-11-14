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

    kosmos 'j.data.bcdb.test(name="sqlitestor_base")'

    use a bcdb which is using sqlite

    """

    bcdb, _ = self._load_test_model(type="sqlite")

    mpath = self._dirpath + "/tests/models"
    assert j.sal.fs.exists(mpath)

    # make sure we remove the maybe already previously generated model file
    for item in j.sal.fs.listFilesInDir(mpath, filter="*.py"):
        j.sal.fs.remove(item)

    bcdb.models_add(mpath)
    model = bcdb.model_get(url="jumpscale.bcdb.test.house")
    assert model.find() == []

    model_obj = model.new()
    model_obj.cost = "10 USD"
    model_obj.save()
    # model.cache_reset()
    data = model.get(model_obj.id)
    assert data.cost_usd == 10
    assert model_obj.cost_usd == 10

    # model.cache_reset()
    model_obj.cost = "11 USD"
    model_obj.save()
    data = model.get(model_obj.id)
    # is with cash
    assert data.cost_usd == 11
    # model.cache_reset()

    # assert model.obj_cache == {}  # cache needs to be empty
    data = model.get(model_obj.id)
    assert data.cost_usd == 11
    # assert model.obj_cache != {}  # now there needs to be something in, WE DONT USE FOR NOW

    # model.cache_reset()
    model_obj = model.new()
    model_obj.name = "TEST"
    model_obj.cost = "12 USD"
    model_obj.save()
    # assert model.obj_cache != {}  # now there needs to be something in WE DONT USE FOR NOW

    assert model_obj.id == 2

    model.get(1)._ddict == {"name": "", "active": False, "cost": b"\x00\x97\x0b\x00\x00\x00", "room": [], "id": 2}

    model.get(2)._ddict == {"name": "", "active": False, "cost": b"\x00\x97\x0c\x00\x00\x00", "room": [], "id": 2}
    model.destroy()

    # assert model.index.select().first().cost == 11.0  # is always in usd

    print("TEST FOR MODELS DONE in SQLITE")
    self._log_info("TEST SQLITE DONE")
    return "OK"
