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
        . {DIR_BASE}/env.sh;
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
        j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeout=15)

        if zdb:
            cl = j.clients.zdb.client_get(name="test", namespace="test_zdb", port=9901)

        # schema = j.core.text.strip(schema)
        # m = bcdb.model_get(schema=schema)

        def get_obj(i):
            schema_obj = m.new()
            schema_obj.nr = i
            schema_obj.name = "somename%s" % i
            schema_obj.date_start = j.data.time.epoch
            schema_obj.email = "info%s@something.com" % i
            return schema_obj

        redis_cl = j.clients.redis.get(ipaddr="localhost", port=6380)

        key = f"{bcdb.name}:data:despiegk.test2"

        for i in range(1, 11):
            print(i)
            o = get_obj(i)
            print("set model 1:despiegk.test2 num:%s" % i)
            redis_cl.execute_command('hsetnew',key, "0", o._json)

        assert redis_cl.hlen(key) == 10

        for i in range(1, 11):
            print(redis_cl.hget(key, i))


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
        name** = ""
        email** = ""
        nr** =  0
        date_start** =  0 (D)
        description = ""
        cost_estimate = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        """

    zdb_test(schema)
    sqlite_test(schema)
    rdb_test(schema)

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
