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

    kosmos 'j.data.bcdb.test(name="acls")'

    test around acls

    """

    def test(name):
        if name == "RDB":
            sqlitestor = False
            rdbstor = True
        elif name == "ZDB":
            sqlitestor = False
            rdbstor = False
        elif name == "SQLITE":
            sqlitestor = True
            rdbstor = False
        else:
            raise j.exceptions.Base("not supported type")

        def load(schema):

            # don't forget the record 0 is always a systems record

            db, model = self._load_test_model(type=name, schema=schema)

            return db, model

        schema = """
            @url = despiegk.test5.acl
            name = "" 
            an_id = 0
            """
        bcdb, m = load(schema)

        self._log_info("POPULATE DATA")

        for i in range(10):
            u = bcdb.user.new()
            u.name = "ikke_%s" % i
            u.email = "user%s@me.com" % i
            u.dm_id = "user%s.ibiza" % i
            u.save()

        for i in range(10):
            g = bcdb.circle.new()
            g.name = "gr_%s" % i
            g.email = "circle%s@me.com" % i
            g.dm_id = "circle%s.ibiza" % i
            g.circle_members = [x for x in range(12, 14)]
            g.user_members = [x for x in range(1, i + 1)]
            g.save()

        assert len(bcdb.user.find()) == 10
        assert len(bcdb.circle.find()) == 10
        assert len([i for i in bcdb.circle.index._id_iterator()]) == 10

        self._log_info("ALL DATA INSERTED (DONE)")

        self._log_info("walk over all data")
        l = bcdb.get_all()

        self._log_info("walked over all data (DONE)")

        assert len(l) == 20
        assert bcdb.acl.autosave is False

        a = m.new()
        a.name = "aname"

        change = a.acl.rights_set(userids=[1], circleids=[12, 13], rights="rw")
        assert change is True

        a.save()

        # means we have indeed the index for acl == 1
        assert len(bcdb.acl.find()) == 1

        self._log_debug("MODIFY RIGHTS")
        a.acl.rights_set(userids=[1], rights="r")
        a.save()

        assert len(bcdb.acl.find()) == 1  # there needs to be a new acl

        assert a.acl.rights_check(1, "r") is True
        assert a.acl.rights_check(1, "d") is False

        a.acl.rights_set([1], [], "rw")
        # users rights_check
        assert a.acl.rights_check(1, "r") is True
        assert a.acl.rights_check(1, "w") is True
        assert a.acl.rights_check(1, "rw") is True
        assert a.acl.rights_check(1, "rwd") is False
        assert a.acl.rights_check(1, "d") is False
        assert a.acl.rights_check(2, "r") is False
        assert a.acl.rights_check(5, "w") is False

        # groups right_check
        assert a.acl.rights_check(12, "rw") is True
        assert a.acl.rights_check(13, "w") is True
        assert a.acl.rights_check(18, "rw") is False
        assert a.acl.rights_check(11, "rw") is False

        a.save()

        self._log_info("TEST ACL DONE: %s" % name)

    test("RDB")
    test("SQLITE")

    self._log_info("ACL TESTS ALL DONE")
