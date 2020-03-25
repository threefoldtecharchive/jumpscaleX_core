from Jumpscale import j
from unittest import TestCase

import redis
import time

"""
try redis commands to get to BCDB
"""
skip = j.baseclasses.testtools._skip


def test_redis():

    """
    to run:

    kosmos 'j.data.bcdb.test(name="redisserver")'

    """

    def do(type="zdb"):
        # CLEAN STATE
        db, model = j.data.bcdb._test_redisserver_get()

        def get_obj(i):
            schema_obj = model.new()
            schema_obj.nr = i
            schema_obj.name = "somename%s" % i
            schema_obj.date_start = j.data.time.epoch
            schema_obj.email = "info%s@something.com" % i
            return schema_obj

        redis_cl = j.clients.redis.get(addr="localhost", port=6381)

        key = f"test_sqlite:data:despiegk.test2"

        for i in range(1, 11):
            print(i)
            o = get_obj(i)
            print("set model 1:despiegk.test2 num:%s" % i)
            redis_cl.execute_command("hsetnew", key, "0", o._json)

        assert redis_cl.hlen(key) == 10

        for i in range(1, 11):
            print(redis_cl.hget(key, i))
        key = f"test_sqlite:data:despiegk.test2"
        redis_cl.hdel(key, 1)
        assert redis_cl.hlen(key) == 9
        db.destroy()

    do(type="rdb")
    do(type="zdb")
    do(type="sqlite")
    j.data.bcdb._log_debug("TEST OK")

    return "OK"
