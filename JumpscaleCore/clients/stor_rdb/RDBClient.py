from Jumpscale import j
import redis

JSBASE = j.baseclasses.object

# TODO: implementation below is not ok, there can be raceconditions if multiple clients connect to redis at the same time
# because we are independently updating the IDVALUE and the hset, this needs to be done by means of a lua stored procedure
# but for now prob ok, especially when used in read mode e.g. in myworker


class RDBClient(j.baseclasses.object_config):

    _SCHEMATEXT = """
    @url = jumpscale.rdb.client
    name** = "" (S)
    nsname = "" (S)
    type = "RDB" (S)
    """

    def _init(self, **kwargs):
        """
        is connection to RDB
        """
        if "redisclient" in kwargs:
            self._redis = kwargs["redisclient"]
        else:
            self._redis = j.clients.redis.get()
        self.type = self.type
        self.nsname = self.nsname
        self._logger_enable()
        self._hsetkey = "rdb:%s" % self.nsname
        self._incrkey = "rdbmeta:incr:%s" % self.nsname
        self._keysbinkey = "rdbmeta:keys:%s" % self.nsname

        assert self.ping()

    def _incr(self):
        return self._redis.incr(self._incrkey) - 1

    def _key_encode(self, key):
        return key

    def _key_decode(self, key):
        return key

    def _value_encode(self, val):
        assert isinstance(val, bytes)
        return j.data.time.epoch.to_bytes(4, "little", signed=False) + val

    def _value_decode(self, val):
        assert isinstance(val, bytes)
        return val[4:]

    def set(self, data, key=None):
        data2 = self._value_encode(data)
        if key in ["", None]:
            # need to increment
            key = self._incr()
        else:
            dataexisting = self.get(key)
            # if data is same then need to return None
            if dataexisting:
                if dataexisting == data:
                    return
        self._redis.execute_command("HSET", self._hsetkey, key, data2)
        return key

    def get(self, key):
        if not key or not isinstance(key, int):
            key = j.data.types.int.clean(key)
        data = self._redis.execute_command("HGET", self._hsetkey, key)
        if not data:
            return None
        data = self._value_decode(data)
        return data

    def exists(self, key):
        if not key or not isinstance(key, int):
            raise j.exceptions.Value("key must be provided, and must be an int")
        return self._redis.execute_command("HEXISTS", self._hsetkey, key) == 1

    def delete(self, key):
        if not key or not isinstance(key, int):
            if not key is 0:
                raise j.exceptions.Value("key must be provided, and must be an int")
        self._redis.execute_command("HDEL", self._hsetkey, key)

    def flush(self):
        """
        will remove all data from the database DANGEROUS !!!!
        :return:
        """
        self._redis.delete(self._hsetkey)
        self._redis.delete(self._incrkey)
        self._redis.delete(self._keysbinkey)

    @property
    def nsinfo(self):
        return {"entries": self.count}

    def list(self, key_start=None, reverse=False):
        """
        list all the keys in the namespace

        :param key_start: if specified start to walk from that key instead of the first one, defaults to None
        :param key_start: str, optional
        :param reverse: decide how to walk the namespace
                        if False, walk from older to newer keys
                        if True walk from newer to older keys
                        defaults to False
        :param reverse: bool, optional
        :return: list of keys
        :rtype: [str]
        """
        result = []
        for key, data in self.iterate(key_start=key_start, reverse=reverse, keyonly=False):
            result.append(key)
        return result

    def iterate(self, key_start=None, reverse=False, keyonly=False):
        """
        walk over all the namespace and yield (key,data) for each entries in a namespace

        :param key_start: if specified start to walk from that key instead of the first one, defaults to None
        :param key_start: str, optional
        :param reverse: decide how to walk the namespace
                if False, walk from older to newer keys
                if True walk from newer to older keys
                defaults to False
        :param reverse: bool, optional
        :param keyonly: [description], defaults to False
        :param keyonly: bool, optional
        :raises e: [description]
        """

        if key_start is None:
            key_start = 0
        else:
            assert isinstance(key_start, int)

        stop = self._redis.get(self._incrkey)
        if not stop:
            stop = 0
        else:
            stop = int(stop) + 1

        if reverse:
            j.shell()
            for i in range(key_start, stop):
                data = self.get(i)
                if data:
                    if keyonly:
                        yield i
                    else:
                        yield (i, data)
        else:
            for i in range(key_start, stop):
                data = self.get(i)
                if data:
                    if keyonly:
                        yield i
                    else:
                        yield (i, data)

    def stop(self):
        pass

    @property
    def count(self):
        """
        :return: return the number of entries in the namespace
        :rtype: int
        """
        return self._redis.hlen(self._hsetkey)

    def ping(self):
        """
        :return:
        """
        return self._redis.ping()
