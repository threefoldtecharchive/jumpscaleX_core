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
    kosmos 'j.data.bcdb.test(name="redis_index_lost")'

    """

    SCHEMA = """
    @url = threefoldtoken.wallet.test
    name* = "wallet"
    addr = ""                   # Address
    ipaddr = (ipaddr)           # IP Address
    email = "" (S)              # Email address
    username = "" (S)           # User name
    
    """

    bcdb = j.data.bcdb.new("test", reset=True)
    m = bcdb.model_get(schema=SCHEMA)
    for i in range(10):
        o = m.new()
        assert o._model.schema.url == "threefoldtoken.wallet.test"
        o.addr = "something:%s" % i
        o.email = "myemail"
        o.name = "myuser_%s" % i
        o.save()

    # we now have some data
    assert len(m.find()) == 10
    r = m.get_by_name("myuser_8")
    assert r[0].addr == "something:8"

    assert "test" in j.data.bcdb._config

    # j.data.bcdb.bcdb_instances = {}  # make sure we don't have instances in memory
    keylength_before = len(j.core.db.keys())
    m.index.destroy()
    keylength_after = len(j.core.db.keys())
    assert keylength_after < keylength_before
    assert len(m.find()) == 0
    bcdb.index_rebuild()
    assert keylength_before == len(j.core.db.keys())
    # stop redis

    # j.core.redistools.core_stop()
    # assert j.core.redistools.core_running() == False

    # db = j.core.redistools.core_get()
    # assert j.core.redistools.core_running()

    # check the redis is really empty
    # assert j.core.db.keys() == []

    # bcdb = j.data.bcdb.get("test")
    # m = bcdb.model_get(schema=SCHEMA)

    assert len(m.find()) == 10
    r = m.get_by_name("myuser_8")
    assert r[0].addr == "something:8"

    self._log_info("TEST DONE")
    return "OK"
