from Jumpscale import j
from unittest import TestCase

import redis
import time

"""
try redis commands to get to BCDB
"""
skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/539")
def test_redis():

    """
    to run:

    kosmos 'j.data.bcdb.test(name="redis")'

    """

    def do(type="zdb"):
        # CLEAN STATE
        redis = j.servers.startupcmd.get("redis_6380")
        redis.stop()
        redis.wait_stopped()
        j.servers.zdb.test_instance_stop()
        j.servers.sonic.default.stop()

        cmd = """
                . {DIR_BASE}/env.sh;
                kosmos 'j.data.bcdb._new("test")' # required to generate storcliet, otherwise next line will fail coz no storclient for that db
                kosmos 'j.data.bcdb.get("test").redis_server_start(port=6380)'
                """

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
        db, model = j.data.bcdb._load_test_model(type=type, schema=schema, datagen=False)
        j.data.bcdb._cmd = j.servers.startupcmd.get(name="redis_6380", cmd_start=cmd, ports=[6380], executor="tmux")
        j.data.bcdb._cmd.start()
        j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeout=15)

        def get_obj(i):
            schema_obj = model.new()
            schema_obj.nr = i
            schema_obj.name = "somename%s" % i
            schema_obj.date_start = j.data.time.epoch
            schema_obj.email = "info%s@something.com" % i
            return schema_obj

        redis_cl = j.clients.redis.get(addr="localhost", port=6380)

        key = f"test:data:despiegk.test2"

        for i in range(1, 11):
            print(i)
            o = get_obj(i)
            print("set model 1:despiegk.test2 num:%s" % i)
            redis_cl.execute_command("hsetnew", key, "0", o._json)

        assert redis_cl.hlen(key) == 10

        for i in range(1, 11):
            print(redis_cl.hget(key, i))
        key = f"test:data:despiegk.test2"
        redis_cl.hdel(key, 1)
        assert redis_cl.hlen(key) == 9
        db.destroy()

    do(type="rdb")
    do(type="zdb")
    do(type="sqlite")
    j.data.bcdb._log_debug("TEST OK")

    return "OK"
