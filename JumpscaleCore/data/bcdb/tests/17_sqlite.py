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

    kosmos 'j.data.bcdb.test(name="sqlite")'

    TO SEE THE SQLITE DB USE SOMETHING LIKE 'db browser for sqlite'
    OPEN DATABASE IN /sandbox/var/bcdb/test/sqlite_index.db
    
    """

    SCHEMA = """
    @url = bcdb.tests.sqlite
    name** =  (S)
    &ipaddr** =  (ipaddr)
    nr** = (I)
    abool** = true (B)
    cat** = "red,blue,green" (E)
    cat2** = "slow,fast" (E)  
    subs = (LO) !bcdb.tests.sqlite.sub
    
    @url = bcdb.tests.sqlite.sub
    a = (I)
    b = (I)
    c = (I)                          
    
    
    """

    db, m = self._load_test_model(type="sqlite", schema=SCHEMA)
    bcdb = m.bcdb

    ###EXAMPLE HOW WE CAN USE TRIGGERS ON MODELS TO BUILD E.G. A CUSTOM INDEX
    # make connection to peewee and to the sqlite index
    p = j.clients.peewee
    db = bcdb.sqlite_index_client

    class BaseModel(p.Model):
        class Meta:
            database = db

    class Index_MyTest(BaseModel):
        # see /sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/clients/peewee/PeeweeFactory.py
        # for which fields can be used
        id = p.IntegerField(unique=True)
        nid = p.IntegerField()
        weight = p.IntegerField()
        name = p.TextField(index=False)

    Index_MyTest.create_table(safe=True)
    m.Index_MyTest = Index_MyTest

    def post_save(model, obj, action=None, propertyname=None, kosmosinstance=None):
        # do something e.g. manipulate the data model after storing in BCDB
        if action == "set_post":
            w = 0
            # just shows how we can calculate something from a subobject
            for sub in obj.subs:
                w += sub.a
                w += sub.b
                w += sub.c
            i = model.Index_MyTest.create(id=obj.id, nid=obj.nid, name=obj.name, weight=w)
            i.save()

    m.trigger_add(post_save)

    o = m.new()
    assert o._autosave == False

    count = 10

    for i in range(count):
        o = m.new()
        assert o._autosave == False
        o.name = "name%s" % i
        o.ipaddr = "10.10.10.%s" % i
        o.nr = i

        if float(i / 2) == float(int(i / 2)):
            o.cat = "RED"
            o.cat2 = "SLOW"
            o.abool = True
        else:
            o.cat = "BLUE"
            o.cat2 = "FAST"
            o.abool = False
        for i2 in range(2):
            os = o.subs.new()
            os.a = i
            os.b = i * 2 * i2
            os.c = i * 3 * i2
        o.save()

    # test for unique constraint
    o = m.new()
    o.ipaddr = "10.10.10.%s" % 4
    try:
        o.save()
    except j.exceptions.Input as e:
        error = True
    assert error

    # IS A COMMENT LEFT FOR A BUG TO RESOLVE: https://github.com/threefoldtech/jumpscaleX_core/issues/48
    # in the shell do o.save()
    # j.shell()
    # you will see it does not create a nice error object representation, if you do same error without shell it works
    # o.save()

    res = m.find()
    assert len(res) == count

    res = m.find(name="name2")
    assert len(res) == 1
    o2 = res[0]
    assert o2.name == "name2"

    res = m.find(name="name4", nr=4)
    assert len(res) == 1
    o3 = res[0]
    assert o3.name == "name4"

    res = m.find(abool=1)
    assert len(res) == 5

    res = m.find(abool=True)
    assert len(res) == 5

    res = m.find(abool=True, nr=4)
    assert len(res) == 1

    res = []
    for x in m.iterate():
        res.append(x)
    t = [i.id for i in res]
    assert [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] == t

    # now use all the power from peewee
    Item = m.index.sql
    r = [(item.id) for item in Item.select().where(Item.cat == "BLUE")]
    assert [2, 4, 6, 8, 10] == r

    r = [(item.id) for item in Item.select().where(Item.nr > 4)]
    assert len(r) == 5

    # to manually execute a sql statement:
    m.index.db

    res = m.index.db.execute_sql("select * from %s ;" % m.index.sql_table_name)
    res2 = res.fetchall()
    assert len(res2) == count
    # super easy to do complicated stuff
    assert res2[0] == (1, 1, "name0", "10.10.10.0", 0, 1, "RED", "SLOW")

    # lets now use the other index table which was created/updated using triggers

    r = m.Index_MyTest.select()
    r2 = [item.name for item in r]
    assert len(r2) == 10
    # we have now queried the other index
    # possibilities are endless, you can do join queries, data aggregation ...
    # DO NOTE: the data stored in the SQLITE is NOT encrypted !!!!

    print("TEST OK")
