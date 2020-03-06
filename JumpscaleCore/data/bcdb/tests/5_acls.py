from Jumpscale import j

skip = j.baseclasses.testtools._skip


def test_acls():
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

            db, model = j.data.bcdb._test_model_get(type=name, schema=schema)

            return db, model

        schema = """
            @url = despiegk.test5.acl
            name** = ""
            an_id = 0
            """
        bcdb, m = load(schema)

        j.data.bcdb._log_info("POPULATE DATA")

        for i in range(10):
            u = bcdb.user.new()
            u.name = "ikke_%s" % i
            u.email = "user%s@me.com" % i
            u.dm_id = "user%s.ibiza" % i
            u.threebot_id = "fake.%s.3bot" % i
            u.ipaddr = "122.12.21.22"
            u.save()

        for i in range(10):
            g = bcdb.circle.new()
            g.name = "gr_%s" % i
            g.email = "circle%s@me.com" % i
            g.dm_id = "circle%s.ibiza" % i
            g.circle_members = [x for x in range(12, 14)]
            g.user_members = [x for x in range(1, i + 1)]
            g.threebot_id = "fake2.3bot"
            g.save()

        assert len(bcdb.user.find()) == 10
        assert len(bcdb.circle.find()) == 10
        assert bcdb.circle.index.sql_index_count() == 10

        j.data.bcdb._log_info("ALL DATA INSERTED (DONE)")

        j.data.bcdb._log_info("walk over all data")
        l = bcdb.get_all()

        j.data.bcdb._log_info("walked over all data (DONE)")

        assert len(l) == 20

        a = m.new()
        a.name = "aname"
        change = a.acl.rights_add(userids=[1], circleids=[12, 13], rights=["r", "w"])
        assert change is True

        a.save()

        # means we have indeed the index for acl == 1
        assert len(bcdb.acl.find()) == 1

        j.data.bcdb._log_debug("MODIFY RIGHTS")
        a.acl.rights_delete(userids=[1], rights=["w"])
        a.save()

        a.acl.rights_add(circleids=[12, 13], rights=["w"])
        a.save()

        assert len(bcdb.acl.find()) == 1  # there needs to be a new acl
        assert a.acl.rights_check(1, ["r"]) is True
        assert a.acl.rights_check(1, ["w"]) is True
        assert a.acl.rights_check(1, ["d"]) is False
        # as user 2 is part of circle 13 it should be the same
        assert a.acl.rights_check(2, ["r"]) is True
        assert a.acl.rights_check(2, ["w"]) is True
        assert a.acl.rights_check(2, ["d"]) is False

        a.acl.rights_add([1], [], ["r", "w"])
        # users rights_check
        assert a.acl.rights_check(1, ["r"]) is True
        assert a.acl.rights_check(1, ["w"]) is True
        assert a.acl.rights_check(1, ["r", "w"]) is True
        assert a.acl.rights_check(1, ["r", "w", "d"]) is False
        assert a.acl.rights_check(1, ["d"]) is False
        assert a.acl.rights_check(2, ["r"]) is True
        assert a.acl.rights_check(5, ["w"]) is False

        # groups right_check
        assert a.acl.rights_check(12, ["r", "w"]) is True
        assert a.acl.rights_check(13, ["w"]) is True
        assert a.acl.rights_check(13, ["r"]) is True
        assert a.acl.rights_check(18, ["r", "w"]) is False
        assert a.acl.rights_check(11, ["r", "w"]) is False

        a.save()

        j.data.bcdb._log_info("TEST ACL DONE: %s" % name)

    def test2(name):
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

            db, model = j.data.bcdb._test_model_get(type=name, schema=schema)

            return db, model

        schema = """
            @url = despiegk.test5.acl
            name** = ""
            an_id = 0
            """
        bcdb, m = load(schema)

        j.data.bcdb._log_info("POPULATE DATA")
        user_ids = []
        for i in range(10):
            u = bcdb.user.new()
            u.name = "testing_%s" % i
            u.email = "user%s@me.com" % i
            u.dm_id = "user%s.ibiza" % i
            u.threebot_id = "fake.%s.3bot" % i
            u.ipaddr = "10.10.10.10"
            u.save()
            user_ids.append(u.id)

        circle_admins = bcdb.circle.new()
        circle_admins.name = "admins"
        circle_admins.email = "admina@me.com"
        circle_admins.dm_id = "admins.ibiza"
        circle_admins.user_members = user_ids[4]
        circle_admins.threebot_id = "fake.134.3bot"
        circle_admins.save()

        circle_publishers = bcdb.circle.new()
        circle_publishers.name = "publishers"
        circle_publishers.email = "publishers@me.com"
        circle_publishers.dm_id = "publishers.ibiza"
        circle_publishers.user_members = user_ids[2:4]
        circle_publishers.circle_members = [circle_admins.id]
        circle_publishers.threebot_id = "fake.135.3bot"
        circle_publishers.save()

        circle_guests = bcdb.circle.new()
        circle_guests.name = "guests"
        circle_guests.email = "guests@me.com"
        circle_guests.dm_id = "guests.ibiza"
        circle_guests.user_members = user_ids[0:2]
        circle_guests.circle_members = [circle_publishers.id]
        circle_guests.threebot_id = "fake.136.3bot"
        circle_guests.save()

        aa = m.new()
        aa.name = "aname"
        aa.save()

        aa.acl.rights_add(userids=user_ids[5:7], circleids=[circle_guests.id], rights=["r"])
        aa.acl.rights_add(userids=user_ids[7:9], circleids=[circle_publishers.id], rights=["w"])
        aa.acl.rights_add(userids=[user_ids[9]], circleids=[circle_admins.id], rights=["d"])

        assert aa.acl.rights_check(user_ids[4], ["r"])
        assert aa.acl.rights_check(user_ids[4], ["d"])
        assert not aa.acl.rights_check(user_ids[2], ["d"])

        assert aa.acl.rights_check(circle_admins.id, ["r"])
        assert aa.acl.rights_check(circle_publishers.id, ["r"])
        assert aa.acl.rights_check(circle_guests.id, ["r"])

        assert aa.acl.rights_check(circle_admins.id, ["w"])
        assert aa.acl.rights_check(circle_publishers.id, ["w"])
        assert aa.acl.rights_check(circle_guests.id, ["w"]) is False

        assert aa.acl.rights_check(circle_admins.id, ["d"])
        assert aa.acl.rights_check(circle_publishers.id, ["d"]) is False
        assert aa.acl.rights_check(circle_guests.id, ["d"]) is False

    test("RDB")
    test("SQLITE")

    test2("RDB")
    test2("SQLITE")

    j.data.bcdb._log_info("ACL TESTS ALL DONE")
