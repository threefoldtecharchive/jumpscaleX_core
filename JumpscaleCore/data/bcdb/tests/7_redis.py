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

    def load(schema, type="zdb"):
        # CLEAN STATE
        j.servers.zdb.test_instance_stop()
        j.servers.sonic.default.stop()

        redis = j.servers.startupcmd.get("redis_6380")
        redis.stop()
        redis.wait_stopped()

        type = type.lower()

        def startZDB():
            zdb = j.servers.zdb.test_instance_start()
            storclient_admin = zdb.client_admin_get()
            assert storclient_admin.ping()
            secret = "1234"
            storclient = storclient_admin.namespace_new(name="test_zdb", secret=secret)
            return storclient

        if type == "rdb":
            j.core.db
            storclient = j.clients.rdb.client_get(namespace="test_rdb")  # will be to core redis
            bcdb = self.get(name="test", storclient=storclient, reset=True)
        elif type == "sqlite":
            storclient = j.clients.sqlitedb.client_get(namespace="test_sdb")
            bcdb = self.get(name="test", storclient=storclient, reset=True)
        elif type == "zdb":
            storclient = startZDB()
            storclient.flush()
            assert storclient.nsinfo["public"] == "no"
            assert storclient.ping()
            bcdb = self.get(name="test", storclient=storclient, reset=True)
        else:
            raise j.exceptions.Base("only rdb,zdb,sqlite for stor")

        cmd = (
            """
                       . {DIR_BASE}/env.sh;
                       kosmos 'j.data.bcdb.get(name="%s").redis_server_start(port=6380)'
                       """
            % type
        )

        self._cmd = j.servers.startupcmd.get(name="redis_6380", cmd_start=cmd, ports=[6380], executor="tmux")
        self._cmd.start()
        j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeout=15)

        assert bcdb.storclient == storclient

        assert bcdb.name == "test"

        # bcdb.reset()  # empty

        assert bcdb.storclient.count == 0

        assert bcdb.name == "test"

        model = bcdb.model_get(schema=schema)

        return bcdb, model

    def do(schema, type="zdb"):

        bcdb, model = load(schema=schema, type=type)

        def get_obj(i):
            schema_obj = model.new()
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
            redis_cl.execute_command("hsetnew", key, "0", o._json)

        assert redis_cl.hlen(key) == 10

        for i in range(1, 11):
            print(redis_cl.hget(key, i))

        key = f"{bcdb.name}:data:despiegk.test2"
        redis_cl.hdel(key, 1)
        assert redis_cl.hlen(key) == 9

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

    do(schema, type="zdb")
    do(schema, type="rdb")
    do(schema, type="sqlite")

    # CLEAN STATE
    j.servers.zdb.test_instance_stop()
    j.servers.sonic.default.stop()
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
