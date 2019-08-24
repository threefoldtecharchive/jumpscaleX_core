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

    kosmos 'j.data.bcdb.test(name="meta_test")'

    """

    bcdb, _ = self._load_test_model()

    assert len(bcdb.get_all()) == 0
    assert len(bcdb.meta._data["url"]) == 7

    s = list(j.data.schema._url_to_md5.keys())

    assert "despiegk.test" in s

    m = bcdb.model_get(url="despiegk.test")

    schema_text = """
    @url = jumpscale.schema.test.a
    category*= ""
    txt = ""
    i = 0
    """
    s = bcdb.schema_get(schema=schema_text)

    assert s.properties_unique == []

    bcdb.meta._schema_set(s)

    assert len(bcdb.meta._data["url"]) == 8

    assert "jumpscale.schema.test.a" in j.data.schema._url_to_md5
    assert "jumpscale.bcdb.circle.2" in j.data.schema._url_to_md5

    schema = bcdb.model_get(url="jumpscale.schema.test.a")
    o = schema.new()

    assert "jumpscale.schema.test.a" in j.data.schema._url_to_md5
    assert "jumpscale.bcdb.circle.2" in j.data.schema._url_to_md5

    s0 = bcdb.schema_get(url="jumpscale.schema.test.a")
    s0md5 = s0._md5 + ""

    model = bcdb.model_get(schema=s0)

    assert bcdb.get_all() == []  # just to make sure its empty

    assert len(bcdb.meta._data["url"]) == 8

    a = model.new()
    a.category = "acat"
    a.txt = "data1"
    a.i = 1
    a.save()

    a2 = model.new()
    a2.category = "acat2"
    a2.txt = "data2"
    a2.i = 2
    a2.save()

    assert len([i for i in model.index._id_iterator()]) == 2

    myid = a.id + 0

    assert a._model.schema._md5 == s0md5

    # lets upgrade schema to float
    s_temp = bcdb.schema_get(schema=schema_text)

    assert len(bcdb.meta._data["url"]) == 8  # should be same because is same schema, should be same md5
    assert s_temp._md5 == s0._md5

    # lets upgrade schema to float
    s2 = bcdb.schema_get(schema=schema_text)

    model2 = bcdb.model_get(schema=s2)

    assert len(bcdb.meta._data["url"]) == 8  # acl, user, circle, despiegktest and the 1 new one

    a3 = model2.new()
    a3.category = "acat3"
    a3.txt = "data3"
    a3.i = 3
    a3.save()
    assert a3.i == 3.0
    assert a2.i == 2  # int

    assert len(model2.find()) == 3  # needs to be 3 because model is for all of them
    assert len(model.find()) == 3  # needs to be 3 because model is for all of them

    all = model2.find()
    print(all)
    a4 = model2.get(all[0].id)
    a4_ = model.get(all[0].id)
    assert a4_ == a4
    a5 = model2.get(all[1].id)
    a6 = model.get(all[2].id)
    a6_ = model.get(all[2].id)
    assert a6_ == a6

    assert a6.id == a3.id
    assert a6.i == a3.i

    self._log_info("TEST META DONE")
    return "OK"
