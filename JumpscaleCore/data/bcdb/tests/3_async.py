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

    kosmos 'j.data.bcdb.test(name="async")'

    this is a test where we use the queuing mechanism for processing data changes

    """

    _, model = self._load_test_model()

    def get_obj(i):
        model_obj = model.new()
        model_obj.nr = i
        model_obj.name = "somename%s" % i
        return model_obj

    model_obj = get_obj(1)

    # should be empty
    assert model.bcdb.queue.empty() is True

    model.set_dynamic(model_obj)
    model_obj2 = model.get(model_obj.id)
    assert model_obj2._ddict_hr == model_obj._ddict_hr

    # will process 1000 obj (set)
    for x in range(100):
        model.set_dynamic(get_obj(x))

    # should be nothing in queue
    assert model.bcdb.queue.empty() is True

    # now make sure index processed and do a new get
    model.index_ready()

    model_obj2 = model.get(model_obj.id)
    assert model_obj2._ddict_hr == model_obj._ddict_hr

    assert model.bcdb.queue.empty()

    self._log_info("TEST ASYNC DONE")

    return "OK"
