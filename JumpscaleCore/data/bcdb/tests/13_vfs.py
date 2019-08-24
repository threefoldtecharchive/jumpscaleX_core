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
from unittest import TestCase


def main(self):
    """
    to run:
    kosmos 'j.data.bcdb.test(name="vfs")'

    """

    SCHEMA = """
    @url = threefoldtoken.wallet.test
    name* = "wallet"
    addr = ""                   # Address
    ipaddr = (ipaddr)           # IP Address
    email = "" (S)              # Email address
    username = "" (S)           # User name
    
    """
    # md5 = "cbf134f55d0c7149ef188cf8a52db0eb"
    # sid = "7"

    bcdb = j.data.bcdb.get("test", reset=True)

    vfs = j.data.bcdb._get_vfs()

    m_wallet_test = bcdb.model_get(schema=SCHEMA)
    test_case = TestCase()
    for i in range(10):
        o = m_wallet_test.new()
        assert o._model.schema.url == "threefoldtoken.wallet.test"
        o.addr = "something:%s" % i
        o.email = "myemail%s@test.fr" % i
        o.name = "myuser_%s" % i
        o.username = "nothing here_%s" % i
        o.save()

    # we now have some data
    assert len(m_wallet_test.find()) == 10
    r = m_wallet_test.get_by_name("myuser_8")
    assert r[0].addr == "something:8"

    r = vfs.get("/")
    bcdb_names = [i for i in r.list()]

    assert "test" in bcdb_names
    r = vfs.get("/test")
    indentifiers = [i for i in r.list()]
    print(indentifiers)
    assert "data" in indentifiers

    r = vfs.get("/test/data")
    namespaces = [i for i in r.list()]

    assert "system" in bcdb_names
    r = vfs.get("/system/data")
    namespaces = [i for i in r.list()]
    print("namespaces:%s" % namespaces)
    assert "1" in namespaces

    vfs.delete("/")
    self._log_info("TEST ROOT DIR DONE")

    with test_case.assertRaises(Exception):
        r = vfs.get("test/schema/md5")
        r = vfs.get("schemas/1")
        r = vfs.get("test/schema/sid/5/78")
        r = vfs.get("test/data/md5")
        r = vfs.get("test/data/2/md6")

    self._log_info("TEST DELETE DATA DONE")

    r = vfs.get("test/data/1")
    identifier_folders = [i for i in r.list()]
    assert len(identifier_folders) > 3
    r = vfs.get("data/1")  # current bcdb is test do to last test
    urls = [i for i in r.list()]
    print("urls:%s" % urls)
    assert (
        "jumpscale.bcdb.circle.2" in urls
        and "jumpscale.bcdb.acl.circle.2" in urls
        and "threefoldtoken.wallet.test" in urls
    )

    r = vfs.get("/data/1/threefoldtoken.wallet.test/")

    objs_from_test_wallet = [i for i in r.list()]
    assert len(objs_from_test_wallet) == 10
    for o in objs_from_test_wallet:
        obj = j.data.serializers.json.loads(o)
        if obj["addr"] == "something:5":
            assert obj["name"] == "myuser_5"
            obj_id_5 = obj["id"]
        if obj["addr"] == "something:4":
            assert obj["name"] == "myuser_4"
            obj_id_4 = obj["id"]
        if obj["addr"] == "something:3":
            assert obj["name"] == "myuser_3"
            obj_id_3 = obj["id"]
        if obj["addr"] == "something:2":
            assert obj["name"] == "myuser_2"
            obj_id_2 = obj["id"]
        if obj["addr"] == "something:1":
            assert obj["name"] == "myuser_1"
            obj_id = obj["id"]

    r = vfs.get("/data/1/threefoldtoken.wallet.test/%s" % obj_id)

    obj = j.data.serializers.json.loads(r.get())

    assert obj["id"] == obj_id
    assert str(obj["addr"]).startswith("something:")
    assert str(obj["name"]).startswith("myuser_")

    self._log_info("TEST GET DATA DONE")

    # schema path
    r3 = vfs.get("schemas/")
    schemas3 = [i for i in r3.list()]

    print(schemas3)
    assert len(schemas3) >= 7
    assert "threefoldtoken.wallet.test" in schemas3  # multiple url link to the same schema id ?

    r = vfs.get("schemas/threefoldtoken.wallet.test")
    schema = r.get()
    obj = j.data.serializers.json.loads(schema)
    assert str(obj["url"]) == "threefoldtoken.wallet.test"
    assert "ipaddr" in str(obj.values())

    self._log_info("TEST GET SCHEMA DONE")

    SCHEMAS = """
    @url = ben.pc.test
    description* = "top_pc"
    cpu = "6ghz" (S)            # power
    ram =  (LI)                   
    enable = true (B)  
    @url = ben.pc.test.2
    description* = "super_top_pc"
    cpu = "12ghz" (S)            # power
    ram =  (LI)                   
    enable = false (B)            
    """
    res = vfs.add_schemas(SCHEMAS)
    assert len(res) == 2

    s1 = vfs.get("schemas/%s" % (res[1].url))
    s2 = vfs.get("schemas/%s" % (res[0].url))
    obj1 = j.data.serializers.json.loads(s1.get())
    obj2 = j.data.serializers.json.loads(s2.get())
    assert obj1["url"] == "ben.pc.test" or obj1["url"] == "ben.pc.test.2"
    assert obj2["url"] == "ben.pc.test" or obj2["url"] == "ben.pc.test.2"

    s = vfs.get("schemas/ben.pc.test")
    obj = j.data.serializers.json.loads(s.get())
    assert obj["url"] == "ben.pc.test"
    sch_dir = vfs.get("data/1")
    assert "ben.pc.test.2" in [i for i in sch_dir.list()]
    self._log_info("TEST SET SCHEMAS DONE")

    # defining a new object based on model url threefoldtoken.wallet.test
    def get_obj(i):
        model_obj = m_wallet_test.new()
        model_obj.addr = "a very very long address that you can easily spot"
        model_obj.email = "ben%s@threefoldtech.com" % i
        model_obj.username = "incredible_username%s" % i
        return model_obj

    model_obj = get_obj(1)

    r3 = vfs.get("data/1/threefoldtoken.wallet.test/%s" % obj_id_3)
    obj3raw = r3.get()
    obj3 = j.data.serializers.json.loads(obj3raw)
    assert obj3["id"] == obj_id_3
    assert obj3["email"] == "myemail3@test.fr"
    assert obj3["username"] == "nothing here_3"

    # let's try to overwrite the data
    t3 = r3.set(model_obj)
    # let's try to get via get
    obj3 = j.data.serializers.json.loads(r3.get())
    assert obj3["id"] == obj_id_3 == t3.id
    assert obj3["email"] == "ben1@threefoldtech.com"
    assert obj3["username"] == "incredible_username1"
    # let's try to get via path
    r3 = vfs.get("data/1/threefoldtoken.wallet.test/%s" % t3.id)
    obj3raw = r3.get()
    obj3 = j.data.serializers.json.loads(obj3raw)
    assert obj3["id"] == obj_id_3 == t3.id
    assert obj3["email"] == "ben1@threefoldtech.com"
    assert obj3["username"] == "incredible_username1"

    # let's try to add new data
    model_new_objs = [get_obj(81), get_obj(18)]
    vfs.add_datas(model_new_objs, 1, "threefoldtoken.wallet.test")

    # we should be able to find the object via url
    r4 = vfs.get("data/1/threefoldtoken.wallet.test/")
    obj_ids = [i for i in r4.list()]

    for o in obj_ids:
        obj = j.data.serializers.json.loads(o)
        if obj["email"] == "ben81@threefoldtech.com":
            assert obj["username"] == "incredible_username81"
            obj_id_81 = obj["id"]
        if obj["email"] == "ben18@threefoldtech.com":
            assert obj["username"] == "incredible_username18"
            obj_id_18 = obj["id"]
    assert obj_id_18
    assert obj_id_81

    # let's try to add new data from directory
    model_new_objs = [get_obj(42), get_obj(24)]
    r4 = vfs.get("data/1/threefoldtoken.wallet.test")
    res = r4.set(model_new_objs)

    # we should be able to find the same object  url
    r4 = vfs.get("data/1/threefoldtoken.wallet.test/")
    obj_ids = [i for i in r4.list()]

    for o in obj_ids:
        obj = j.data.serializers.json.loads(o)
        if obj["email"] == "ben42@threefoldtech.com":
            assert obj["username"] == "incredible_username42"
            obj_id_42 = obj["id"]
        if obj["email"] == "ben24@threefoldtech.com":
            assert obj["username"] == "incredible_username24"
            obj_id_24 = obj["id"]
    assert obj_id_42
    assert obj_id_24

    self._log_info("TEST SET DATA DONE")
    r = vfs.get("data/1/threefoldtoken.wallet.test/%s" % obj_id)
    obj = r.get()
    r.delete()
    schema_wallet_obj = j.data.serializers.json.loads(schema)

    with test_case.assertRaises(Exception) as cm:  # can't delete an already deleted data
        vfs.get("data/1/%s/%s" % (schema_wallet_obj["url"], obj_id))
    ex = cm.exception
    assert "not find obj with id:%s" % obj_id in str(ex.args[0])

    # test delete data form a url get
    r2 = vfs.get("data/1/threefoldtoken.wallet.test/%s" % obj_id_2)
    obj2raw = r2.get()
    obj2 = j.data.serializers.json.loads(obj2raw)
    assert obj2["name"] == "myuser_2"
    assert obj2["id"] == obj_id_2

    removed_obj = r2.delete()
    print("comparing key:%s with key:%s" % (removed_obj.key, r2.key))
    assert removed_obj.key == r2.key

    # test delete all data form a url
    rdelall = vfs.get("data/1/threefoldtoken.wallet.test/")
    objItems = rdelall.items
    removed_objs = rdelall.delete()
    for o in removed_objs:
        assert o.item in objItems

    self._log_info("TEST DELETE DATA DONE")

    # clean state
    vfs.delete("/")
    self._log_info("TEST DONE")
    return "OK"
