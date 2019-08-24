class RedisDict(dict):
    def __init__(self, client, key):
        self._key = key
        self._client = client

    def __getitem__(self, key):
        value = self._client.hget(self._key, key)
        return json.loads(value)

    def __setitem__(self, key, value):
        value = json.dumps(value)
        self._client.hset(self._key, key, value)

    def __contains__(self, key):
        return self._client.hexists(self._key, key)

    def __repr__(self):
        return repr(self._client.hgetall(self._key))

    def copy(self):
        result = dict()
        allkeys = self._client.hgetalldict(self._key)
        for key, value in list(allkeys.items()):
            result[key] = json.loads(value)
        return result

    def pop(self, key):
        value = self._client.hget(self._key, key)
        self._client.hdel(self._key, key)
        return json.loads(value)

    def keys(self):
        return self._client.hkeys(self._key)

    def iteritems(self):
        allkeys = self._client.hgetalldict(self._key)
        for key, value in list(allkeys.items()):
            yield key, json.loads(value)
