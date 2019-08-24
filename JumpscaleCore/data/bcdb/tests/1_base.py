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

    kosmos 'j.data.bcdb.test(name="base")'

    """

    def test(name, schema, sqlite=True):
        def load(schema_url):

            # don't forget the record 0 is always a systems record
            db, model = self._load_test_model(type=name, schema=schema)

            for i in range(10):
                model_obj = model.new()
                model_obj.llist.append(1)
                model_obj.llist2.append("yes")
                model_obj.llist2.append("no")
                model_obj.llist3.append(1.2)
                model_obj.date_start = j.data.time.epoch
                model_obj.U = 1.1
                model_obj.nr = i
                model_obj.token_price = "10 EUR"
                model_obj.description = "something"
                model_obj.name = "name%s" % i
                model_obj.email = "info%s@something.com" % i
                model_obj2 = model.set(model_obj)

            assert len(model.find()) == 10

            model_obj3 = model.get(model_obj2.id)

            assert model_obj3.id == model_obj2.id

            assert model_obj3._ddict == model_obj2._ddict
            assert model_obj3._ddict == model_obj._ddict

            return db

        if sqlite:
            schema_url = "despiegk.test.sqlite"
        else:
            schema_url = "despiegk.test"
        db = load(schema_url)
        db_model = db.model_get(url=schema_url)

        if sqlite:
            query = db_model.index.sql.select()
            qres = [(item.name, item.nr) for item in query]

            assert qres == [
                ("name0", 0),
                ("name1", 1),
                ("name2", 2),
                ("name3", 3),
                ("name4", 4),
                ("name5", 5),
                ("name6", 6),
                ("name7", 7),
                ("name8", 8),
                ("name9", 9),
            ]

            assert db_model.index.sql.select().where(db_model.index.sql.nr == 5)[0].name == "name5"

            query = db_model.index.sql.select().where(db_model.index.sql.nr > 5)  # should return 4 records
            qres = [(item.name, item.nr) for item in query]

            assert len(qres) == 4

            res = db_model.index.sql.select().where(db_model.index.sql.name == "name2")
            assert len(res) == 1
            assert res.first().name == "name2"

            res = db_model.index.sql.select().where(db_model.index.sql.email == "info2@something.com")
            assert len(res) == 1
            assert res.first().name == "name2"

            first_id = res.first().id

        # see that the change of data does not set the _changed_items
        model_obj3 = db_model.find()[2]
        model_obj = db_model.get(model_obj3.id)
        n2 = model_obj.name + ""
        model_obj.name = n2

        # because data did not change, was already that data
        model_obj.name = "name3"

        assert model_obj._ddict["name"] == "name3"

        model_obj.token_price = "10 USD"
        assert model_obj.token_price_usd == 10
        db_model.set(model_obj)
        model_obj2 = db_model.get(model_obj.id)
        assert model_obj2.token_price_usd == 10

        if sqlite:
            assert db_model.index.sql.select().where(db_model.index.sql.id == model_obj.id).first().token_price == 10
        else:
            o = db_model.get_by_name("name1")[0]
            o.name == "name1"

        def do(id, obj, result):
            result[obj.nr] = obj.name
            return result

        result = {}
        for obj in db_model.iterate():
            result[obj.nr] = obj.name

        print(result)
        assert result == {
            0: "name0",
            1: "name1",
            2: "name3",
            3: "name3",
            4: "name4",
            5: "name5",
            6: "name6",
            7: "name7",
            8: "name8",
            9: "name9",
        }

        # assert db_model.index.sql._id_exists(1)
        # assert db_model.index.sql._id_exists(10) == False  #NEEDS TO BE DEBUGGED & IMPROVED

        self._log_info("TEST DONE: %s" % name)

    schema_sqlite = """
    @url = despiegk.test.sqlite
    llist2 = "" (LS)
    name** = ""
    email** = ""
    nr** = 0
    date_start** = 0 (D)
    description = ""
    token_price** = "10 USD" (N)
    hw_cost = 0.0 #this is a comment
    llist = []
    llist3 = "1,2,3" (LF)
    llist4 = "1,2,3" (L)
    llist5 = "1,2,3" (LI)
    U = 0.0
    pool_type = "managed,unmanaged" (E)
    """
    schema = """
    @url = despiegk.test
    llist2 = "" (LS)
    name* = ""
    email* = ""
    nr* = 0
    date_start* = 0 (D)
    description = ""
    token_price* = "10 USD" (N)
    hw_cost = 0.0 #this is a comment
    llist = []
    llist3 = "1,2,3" (LF)
    llist4 = "1,2,3" (L)
    llist5 = "1,2,3" (LI)
    U = 0.0
    pool_type = "managed,unmanaged" (E)
    """

    test("RDB", schema, sqlite=False)

    test("ZDB", schema_sqlite)

    test("SQLITE", schema_sqlite)

    # CLEAN STATE
    self._log_info("TEST BASE DONE")
    return "OK"
