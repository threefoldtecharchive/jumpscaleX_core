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

import redis

"""
try redis commands to get to BCDB
"""


def main(self):

    """
    to run:

    kosmos 'j.data.bcdb.test(name="redis")'

    """

    def do(bcdb, m, zdb=False):
        cmd = """
        . /sandbox/env.sh;
        kosmos 'j.data.bcdb.get("test").redis_server_start(port=6380)'
        """
        test_case = TestCase()
        # WARNING bcdb get rest=true will delete and restore the db file
        # this need to be executed BEFORE the redis server startup as it will connect to the same
        # database and if the file is deleted before we end up with readonly error
        # see https://techblog.dorogin.com/sqlite-error-8-attempt-to-write-a-readonly-database-62b80cc6c9db
        # bcdb = j.data.bcdb.get("test", reset=True)

        self._cmd = j.servers.startupcmd.get(name="redis_6380", cmd_start=cmd, ports=[6380], executor="tmux")
        self._cmd.start()
        j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeoutTotal=15)

        if zdb:
            cl = j.clients.zdb.client_get(name="test", namespace="test_zdb", port=9901)

        # schema = j.core.text.strip(schema)
        # m = bcdb.model_get(schema=schema)

        def get_obj(i):
            schema_obj = m.new()
            schema_obj.nr = i
            schema_obj.name = "somename%s" % i
            return schema_obj

        redis_cl = j.clients.redis.get(ipaddr="localhost", port=6380)

        self._log_debug("set schema to 'despiegk.test2'")
        print(redis_cl.get("schemas"))

        redis_cl.set("schemas:despiegk.test2", m.schema.text)
        print(redis_cl.get("schemas:despiegk.test2"))
        print(redis_cl.get("schemas"))
        for i in range(1, 11):
            print(i)
            o = get_obj(i)
            print("set model 1:despiegk.test2 num:%s" % i)
            redis_cl.set("data:1:despiegk.test2", o._json)

        print(redis_cl.get("data:1:despiegk.test2"))

        self._log_debug("compare schema")
        schema2 = redis_cl.get("schemas:despiegk.test2")
        # test schemas are same

        assert j.data.serializers.json.loads(schema2)["url"] == "despiegk.test2"
        assert j.data.serializers.json.loads(schema2)["llist2"] == "list"
        assert j.data.serializers.json.loads(schema2)["cost_estimate"] == "float"
        # assert redis_cl.hlen("schemas:url") == 9
        assert redis_cl.hlen("schemas:despiegk.test2") == 1
        assert redis_cl.hlen("data:1:despiegk.test2") == 10

        if zdb:
            self._log_debug("validate list")
            print("zbd enabled c list:%s" % cl.list())
            assert len(cl.list()) == 11

        self._log_debug("validate added objects")

        items = redis_cl.get("data:1:despiegk.test2")
        item0 = j.data.serializers.json.loads(items[1][0])
        item1 = j.data.serializers.json.loads(items[1][1])
        print(redis_cl.delete("data:1:despiegk.test2:%s" % item0["id"]))

        print(redis_cl.get("data:1:despiegk.test2:%s" % item1["id"]))
        # it's deleted
        with test_case.assertRaises(Exception) as cm:
            redis_cl.get("data:1:despiegk.test2:%s" % item0["id"])
        ex = cm.exception
        assert "cannot get, key:'data/1/despiegk.test2/%s' not found" % item0["id"] in str(ex.args[0])

        assert redis_cl.hlen("data:1:despiegk.test2:%s" % item1["id"]) == 1

        assert redis_cl.hlen("data:1:despiegk.test2") == 9

        # there should be 10 items now there
        if zdb:
            self._log_debug("validate list2")
            assert len(cl.list()) == 10

        self._cmd.stop()
        self._cmd.wait_stopped()
        return

    def sqlite_test(schema):
        # SQLITE BACKEND
        bcdb, m = self._load_test_model(type="sqlite", schema=schema)
        do(bcdb, m, zdb=False)

    def rdb_test(schema):
        # RDB test
        bcdb, m = self._load_test_model(type="rdb", schema=schema)
        do(bcdb, m, zdb=False)

    def zdb_test(schema):
        # ZDB test
        bcdb, m = self._load_test_model(type="zdb", schema=schema)
        c = j.clients.zdb.client_admin_get(port=9901)
        do(bcdb, m, zdb=True)

    schema = """
        @url = despiegk.test2
        llist2 = "" (LS)
        name* = ""
        email* = ""
        nr* = 0
        date_start* = 0 (D)
        description = ""
        cost_estimate = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        """

    zdb_test(schema)
    rdb_test(schema)
    sqlite_test(schema)

    redis = j.servers.startupcmd.get("redis_6380")
    redis.stop()
    redis.wait_stopped()

    self._log_debug("TEST OK")

    return "OK"


def _compare_strings(s1, s2):
    # TODO: move somewhere into jumpscale tree
    def convert(s):
        if isinstance(s, bytes):
            s = s.decode()
        return s

    return convert(s1).strip() == convert(s2).strip()
