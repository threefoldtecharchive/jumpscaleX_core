from Jumpscale import j


from .Coordinator import Coordinator
from .ServiceBase import ServiceBase
from .ServiceBase2 import ServiceBase2

JSBASE = j.baseclasses.object


class MemUsageTest(j.baseclasses.object):

    __jslocation__ = "j.tools.memusagetest"

    def __init__(self):

        JSBASE.__init__(self)

    @property
    def _service_base_class(self):
        return ServiceBase

    @property
    def _service_base_class2(self):
        return ServiceBase2

    @property
    def _coordinator_base_class(self):
        return Coordinator

    def test_redis_lua_perf(self):

        """
        kosmos 'j.tools.memusagetest.test_redis_lua_perf()'

        FOR RDM:
        socat -v tcp-l:6379,reuseaddr,fork unix:/sandbox/var/redis.sock

        """

        memusage_start = j.application.getMemoryUsage()
        print("MEM USAGE START:%s" % memusage_start)

        def redis_reset():

            j.clients.redis.core_stop()
            r_classic = j.clients.redis.core_get()

            from credis import Connection

            r = Connection(path="/sandbox/var/redis.sock")
            r.connect()
            assert r.execute(b"PING") == b"PONG"

            return r, r_classic

        def script_register(C):
            C = j.core.text.strip(C)
            # assert r_classic.eval(C.encode(),0)==None
            script_hash = r.execute(b"SCRIPT", b"LOAD", C.encode())
            assert r.execute(b"SCRIPT", b"EXISTS", script_hash) == [1]
            return script_hash

        C = """
        local key = tostring(KEYS[1])
        local data = tostring(KEYS[2])
        local r
        local data2
        local lasttime=0
        
        return KEYS[1]
        """
        r, r_classic = redis_reset()
        script_hash = script_register(C)
        assert r.execute(b"EVALSHA", script_hash, 2, b"aa", b"cc") == b"aa"

        j.tools.timer.start("redisperf")

        nritems = 10000

        for item in range(nritems):
            r.execute(b"EVALSHA", script_hash, 2, b"aa", str(item).encode())

        nr = j.tools.timer.stop(nritems)
        assert nr > 20000

        # lets now pipeline

        j.tools.timer.start("redisperf_pipeline_20_per_pack")

        nritems = 100000

        pack = []
        pack_amount = 20
        nr = 0
        for item in range(nritems):
            pack.append((b"EVALSHA", script_hash, 2, b"aa", str(item).encode()))
            nr += 1
            if nr > pack_amount:
                r.execute_pipeline(*pack)
                nr = 0
                pack = []
        r.execute_pipeline(*pack)

        nr = j.tools.timer.stop(nritems)
        assert nr > 100000

        # msgpack performance

        C = """
        local key = tostring(KEYS[1])
        local data = cmsgpack.unpack(KEYS[2])
        local r
        local data2
        local lasttime=0
        
        data2 = redis.sha1hex(data["name"])
        
        return data2
        """

        script_hash = script_register(C)

        j.tools.timer.start("msgpack")

        nritems = 10000

        pack = []
        pack_amount = 20
        nr = 0

        data = {}
        data["name"] = "myname"
        data["name2"] = "myname2"
        data["bool"] = False
        data["list"] = [1, 2, 3, 4]

        print(r.execute(b"EVALSHA", script_hash, 2, b"aa", msgpack.dumps(data)))

        for item in range(nritems):
            data2 = msgpack.dumps(data)  # +400k per sec
            r.execute(b"EVALSHA", script_hash, 2, b"aa", data2)

        nr = j.tools.timer.stop(nritems)
        # assert nr>100000

        # C=j.sal.fs.readFile("%s/test.lua"%self._dirpath)

        r, r_classic = redis_reset()

        pids = j.sal.process.getPidsByFilter("redis-server")
        assert len(pids) == 1

        p = j.sal.process.getProcessObject(pids[0])
        info = p.memory_full_info()

        redis_mem_start = info.uss

        j.tools.timer.start("memusage")

        from nacl.hash import blake2b
        from nacl import encoding
        from pyblake2 import blake2b

        nritems = 100000

        for item in range(nritems):
            hash = blake2b(str(item).encode(), digest_size=10).digest()  # can do 900k per second
            j.shell()
            w
            try:
                r.execute("HSET", hash[0:1], hash[1:], b"aaaa")
            except:
                j.shell()
                e

        j.tools.timer.stop(nritems)

        memusage_stop = j.application.getMemoryUsage()
        print("MEM USAGE STOP:%s" % memusage_stop)
        print("MEM USAGE difference in KB:%s" % (memusage_stop - memusage_start))

        p = j.sal.process.getProcessObject(pids[0])
        info = p.memory_full_info()
        redis_mem_stop = info.uss

        redismem = redis_mem_stop - redis_mem_start

        print("REDIS MEM USAGE difference in KB:%s" % (redismem / 1024))

        print("BYTES PER ITEM IN REDIS: %s" % (redismem / nritems))

        print("CONCLUSION: 30MB for 1m objects index in mem, this gives us 10bytes for the hash")

    def test_unidecode(self):
        """
        kosmos 'j.tools.memusagetest.test_unidecode()'
        """

        j.tools.timer.start("memusage")

        nritems = 10000

        for item in range(nritems):

            j.core.text.strip_to_ascii_dense("IPA Extensionsɐ ɑ ɒ ɓ %s ɔ ɕ ɖ ɗ ɘ ə ɚ ɛ " % item)
            # should try and make this in cython and see how much faster

        # +30k per sec

        res = j.tools.timer.stop(nritems)
        assert res > 20000

    def test_redis_kvs(self):

        """
        kosmos 'j.tools.memusagetest.test_redis_kvs()'
        """

        memusage_start = j.application.getMemoryUsage()
        print("MEM USAGE START:%s" % memusage_start)

        j.clients.redis.core_stop()
        r_classic = j.clients.redis.core_get()

        s = r_classic.register_script("%s/test.lua" % self._dirpath)

        rest = r.evalsha(s.sha, 2, "aaa", "bbb")

        j.shell()

        r = j.data.bcdb.redis

        pids = j.sal.process.getPidsByFilter("redis-server")
        assert len(pids) == 1

        p = j.sal.process.getProcessObject(pids[0])
        info = p.memory_full_info()

        redis_mem_start = info.uss

        j.tools.timer.start("memusage")

        from nacl.hash import blake2b
        from nacl import encoding
        from pyblake2 import blake2b

        nritems = 100000

        for item in range(nritems):
            hash = blake2b(str(item).encode(), digest_size=8).digest()  # can do 900k per second
            try:
                r.execute("HSET", hash[0:2], hash[2:], b"aaaa")
            except:
                j.shell()
                e

        j.tools.timer.stop(nritems)

        memusage_stop = j.application.getMemoryUsage()
        print("MEM USAGE STOP:%s" % memusage_stop)
        print("MEM USAGE difference in KB:%s" % (memusage_stop - memusage_start))

        # p=j.sal.process.getProcessObject(pids[0])
        info = p.memory_full_info()
        redis_mem_stop = info.uss

        print("REDIS MEM USAGE difference in KB:%s" % ((redis_mem_stop - redis_mem_start) / 1024))

    def test_formatter(self):
        """
        kosmos 'j.tools.memusagetest.test_formatter()'
        """

        from string import Formatter

        formatter = Formatter()

        args = {"name": "MYNAME", "val": "AVAL", "n": 1.9998929}

        # res = formatter.format(C,**args)

        C = "{name!s:>10} {val} {n:<10.2f}"  # floating point rounded to 2 decimals
        # python doc: string.Formatter

        j.tools.timer.start("formatter")

        nritems = 100000
        for i in range(nritems):
            if "{" in C:
                C2 = formatter.format(C, **args)

        j.tools.timer.stop(nritems)

        # +100k per sec

    def test(self):
        """
        kosmos 'j.tools.memusagetest.test()'
        """

        memusage_start = j.application.getMemoryUsage()
        print("MEM USAGE START:%s" % memusage_start)

        j.tools.timer.start("memusage")

        # pr = j._profileStart()

        nritems = 1000000

        res = []
        res2 = {}
        for item in range(nritems):
            # res.append("")
            # res.append(self._service_base_class())
            # res.append(self._service_base_class2())
            res2[item] = self._service_base_class()

        # res = j._profileStop(pr)

        j.tools.timer.stop(nritems)

        memusage_stop = j.application.getMemoryUsage()
        print("MEM USAGE STOP:%s" % memusage_stop)

        print("MEM USAGE difference in KB:%s" % (memusage_stop - memusage_start))

        x = (memusage_stop - memusage_start) * 1024 / nritems

        print("mem usage in bytes per class in list:%s" % (x))

        # conclusion: to load 1m classes with static method: 178 bytes per class in mem and speed +1m/sec
        # conclusion: to load 1m classes with normal method: 178 bytes per class in mem and speed +1m/sec
        # conclusion: to load 1m classes with normal method in dict: 250 bytes per class in mem and speed +1m/sec

        # conclusion: 84 bytes per reference in a dict
        # conclusion: 8 bytes per reference in a list

        j.shell()
        w

        hv = j.world.hypervisor
