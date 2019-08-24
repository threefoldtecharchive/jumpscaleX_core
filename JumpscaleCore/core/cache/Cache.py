import pickle
import time


class Cache(object):
    def __init__(self, j):
        self._cache = {}
        self._j = j

    # def serialize(self, val):
    #     tt = self._j.data.types.type_detect(val)

    def get(self, id="main", reset=False, expiration=3600):
        """
        @param id is a unique id for the cache
        db = when none then will be in memory
        """
        if id not in self._cache:
            self._cache[id] = CacheCategory(j=self._j, id=id, expiration=expiration, reset=reset)
            if reset:
                self._cache[id].reset()
        return self._cache[id]

    def resetAll(self):
        for key, cache in self._cache.items():
            cache.reset()

    def reset(self, id=None):
        if id is None:
            self.resetAll()
        else:
            if id in self._cache:
                self._cache[id].reset()

    def _testAll(self, c):
        c.set("something", "OK")
        assert "something" in c.list()
        assert c.exists("something")
        c.reset()
        assert c.exists("something") == False
        c.set("something", "OK")

        self.reset()
        assert c.exists("something") == False

        c.set("something", "OK")
        assert "OK" == c.get("something")

        def return1():
            return 1

        def return2():
            return 2

        def return3():
            return 3

        assert c.get("somethingElse", return1) == 1
        assert c.get("somethingElse") == 1

        c.reset()

        try:
            c.get("somethingElse")
        except Exception as e:
            if "Cannot get 'somethingElse' from cache" not in str(e):
                raise j.exceptions.Base("error in test. non expected output")

        time.sleep(2)

        assert c.get("somethingElse", return2, expire=1) == 2
        # still needs to be 2
        assert c.get("somethingElse", return3, expire=1) == 2
        time.sleep(2)
        assert c.get("somethingElse", return3, expire=1) == 3  # now needs to be 3

        assert c.get("somethingElse", return2, expire=100, refresh=True) == 2
        assert c.exists("somethingElse")
        time.sleep(2)
        assert c.exists("somethingElse")
        assert "somethingElse" in c.list()
        self.reset()
        assert c.exists("somethingElse") == False
        assert "somethingElse" not in c.list()

    def test(self):
        """
        kosmos 'j.core.cache.test()'
        """

        # make sure its redis
        self._j.clients.redis.core_get()
        self._j.core.db_reset()
        c = self.get("test", expiration=1)
        self._testAll(c)
        self._j.tools.tutorial.cache()
        print("CACHE ALL TESTS DONE")

    def test_without_redis(self):
        """ kosmos 'j.core.cache.test_without_redis()'

            NOTE: this test actually stops the redis server
            (and restarts it afterwards).  be careful!
        """

        # now stop redis...
        self._j.clients.redis.kill()
        self._j.core.db_reset()

        c = self.get("test", expiration=1)
        self._testAll(c)
        # ... and restart it again
        self._j.clients.redis.start()


class CacheCategory(object):
    def __init__(self, j, id, expiration=3600, reset=False):
        self._j = j
        self.id = id
        self.db = self._j.core.db
        self.hkey = "cache:%s" % self.id
        self.expiration = expiration
        if reset:
            self.reset()

    def _key_get(self, key):
        return "cache:%s:%s" % (self.id, key)

    def delete(self, key):
        self.db.delete(self._key_get(key))

    def set(self, key, value, expire=None):
        if expire is None:
            expire = self.expiration
        data = pickle.dumps((self._j.data.time.epoch + expire, value))
        self.db.set(self._key_get(key), data, ex=expire)

    def exists(self, key):
        return self.db.get(self._key_get(key)) is not None

    def get(self, key, method=None, expire=None, refresh=False, retry=1, die=True, **kwargs):
        """

        :param key: is a unique key for item to fetch out of the cache
        :param method: the method to execute
        :param expire: expiration in seconds (if 0 then will be same as refresh = True)
        :param refresh: if True will execute again (will be set into local caching DB)
        :param retry: std 1, means will only try 1 time, otherwise will try multiple times,
                    useful for e.g. fetching something from internet
        :param kwargs: the arguments in kwargs form e.g. a="1"  for the method to execute
        :param die, normally True, means will raise error if doesnt work, if False will return the error object
        :return: the output of the method
        """
        if refresh:
            self.delete(key)
            res = None
        else:
            # check if key exists then return (only when no refresh)
            res = self.db.get(self._key_get(key))
            if res is not None:
                expireEpoch, res = pickle.loads(res)
                if self._j.data.time.epoch > expireEpoch:
                    self.delete(key)
                    res = None
                else:
                    # print("cache hit:%s" % key)
                    return res

        if expire is None:
            expire = self.expiration

        # print("key:%s res:%s" % (key, res))
        if method is None:
            raise self._j.exceptions.RuntimeError("Cannot get '%s' from cache,not found & method None" % key)
        # print("cache miss:%s (%s)" % (key, method))
        nr = 0
        while nr < retry:
            try:
                val = method(**kwargs)
                break
            except Exception as e:
                nr += 1
                if nr == retry:
                    if die:
                        raise e
                    else:
                        return e

        # print(val)
        if val is None or val == "":
            raise self._j.exceptions.RuntimeError("cache method cannot return None or empty string.")
        self.set(key, val, expire=expire)
        return val

    def reset(self):
        for item in self.list():
            self.delete(item)

    def list(self):
        return [item.decode().split(":")[-1] for item in self.db.keys("cache:%s:*" % self.id)]

    def __str__(self):
        res = {}
        for key in self.db.keys():
            val = self.db.get(key)
            res[key] = val
        out = self._j.data.serializers.yaml.dumps(res)
        return out

    __repr__ = __str__
