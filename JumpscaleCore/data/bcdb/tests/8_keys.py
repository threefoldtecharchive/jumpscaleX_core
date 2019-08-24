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
    kosmos 'j.data.bcdb.test(name="keys")'

    """

    SCHEMA = """
    @url = threefoldtoken.wallet.test
    name* = "wallet"
    jwt = "" (S)                # JWT Token
    addr* = ""                   # Address
    ipaddr* = (ipaddr)           # IP Address
    email* = "" (S)              # Email address
    username* = "" (S)           # User name
    
    
    """

    db, m = self._load_test_model(type="sqlite", schema=SCHEMA)
    bcdb = m.bcdb

    o = m.new()
    assert o._model.schema.url == "threefoldtoken.wallet.test"
    o.addr = "something"
    o.email = "myemail"
    o.username = "myuser"
    o.save()

    assert o._model.schema.url == "threefoldtoken.wallet.test"

    o2 = m.find(addr=o.addr)[0]
    assert len(m.find(addr=o.addr)) == 1
    o3 = m.find(email=o.email)[0]
    o4 = m.find(username=o.username)[0]

    assert o2.id == o.id
    assert o3.id == o.id
    assert o4.id == o.id

    o = m.new()
    o.name = "test2"
    o.addr = "something2"
    o.email = "myemail2"
    o.username = "myuser"
    o.save()

    o = m.new()
    o.name = "test3"
    o.addr = "something2"
    o.email = "myemail2"
    o.username = "myuser2"
    o.save()

    assert o._model.schema.url == "threefoldtoken.wallet.test"

    l = m.find(username="myuser")
    assert len(l) == 2

    l = m.find(email="myemail2", username="myuser")
    assert len(l) == 1

    assert len(m.find()) == 3
    o_check = m.find()[-1]
    assert o_check.id == o.id

    rkey = m.index._key_index_hsetkey_get()
    o.delete()
    for key in j.clients.credis_core.keys(rkey + ":*"):
        for key2 in j.clients.credis_core.hkeys(key):
            data_ = j.clients.credis_core.hget(key, key2)
            data__ = j.data.serializers.msgpack.loads(data_)
            if o.id in data__:
                raise j.exceptions.Base("the id should not be in the redis index")

    m2 = bcdb.model_get(schema=SCHEMA)

    SCHEMA3 = """
    @url = threefoldtoken.wallet.test2
    name* = "wallet3"
    jwt = "" (S)                # JWT Token
    addr* = "aa"                   # Address
    ipaddr* = "" (ipaddr)           # IP Address
    email* =  (S)              # Email address 
    nr = 10 (I)
    nr2 =  (I)
    nr3 =  (N)
    nr4 = 5 (N)
    date = (D)   
    
    """
    m3 = bcdb.model_get(schema=SCHEMA3)
    o = m3.new()

    # default
    assert o.addr == "aa"
    assert o.ipaddr == "0.0.0.0"
    assert o.email == ""
    assert o.nr == 10
    assert o.nr2 == 2147483647
    assert o.nr3 == b"\x00\x97\x00\x00\x00\x00"
    assert o.nr3_usd == 0
    assert o.nr4_usd == 5
    assert o.date == 0

    o.ipaddr = "192.168.1.1"
    o.email = "ename"
    o.addr = "test"
    o.name = "test2"
    o.save()
    assert o._model.schema.url == "threefoldtoken.wallet.test2"

    assert list(m3.iterate()) == m3.find()

    assert len(m3.find(addr="test")) == 1

    assert len(m3.find(addr="test", email="ename", ipaddr="192.168.1.1")) == 1
    assert len(m3.find(addr="test", email="ename", ipaddr="192.168.1.2")) == 0

    # storclient2 = j.clients.sqlitedb.client_get(namespace="test2_sdb_keys")
    storclient2 = j.clients.rdb.client_get(namespace="test2_sdb_keys")
    storclient2.flush()
    j.data.bcdb.new(name="test2", storclient=storclient2, reset=True)
    bcdb2 = j.data.bcdb.get("test2")
    assert len(m3.find(addr="test", email="ename", ipaddr="192.168.1.1")) == 1
    bcdb2.reset()
    m3.destroy()
    assert len(m3.find(addr="test", email="ename", ipaddr="192.168.1.1")) == 0

    # now we know that the previous indexes where not touched
    m4 = bcdb2.model_get(schema=SCHEMA3)
    o = m4.new()
    o.ipaddr = "192.168.1.1"
    o.email = "ename"
    o.addr = "test"
    o.save()

    assert o._model.schema.url == "threefoldtoken.wallet.test2"

    myid = o.id + 0  # make copy

    assert len(m4.find(addr="test", email="ename", ipaddr="192.168.1.1")) == 1

    o5 = m4.find(addr="test", email="ename", ipaddr="192.168.1.1")[0]
    assert o5.id == myid

    bcdb.reset()
    bcdb2.reset()

    self._log_info("TEST DONE")
    return "OK"
