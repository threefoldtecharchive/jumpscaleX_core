from Jumpscale import j

# import gevent


class RedisCoreClient(j.baseclasses.object):

    __jslocation__ = "j.clients.credis_core"

    def _init(self, **kwargs):
        self._credis = False

        try:
            from credis import Connection

        except (ModuleNotFoundError, ImportError) as e:
            j.builders.runtimes.python3.pip_package_install("credis")
            from credis import Connection

        try:
            self._client = Connection(path="/sandbox/var/redis.sock")
            self._client.connect()
            self._credis = True
        except:
            self._client = j.clients.redis.core_get()

        if self._credis:
            assert self.execute("PING") == b"PONG"
        else:
            assert self.execute("PING")

    def execute(self, *args):
        if self._credis:
            return self._client.execute(*args)
        else:
            return self._client.execute_command(*args)

    def get(self, *args):
        return self.execute("GET", *args)

    def set(self, *args):
        return self.execute("SET", *args)

    def hset(self, *args):
        return self.execute("HSET", *args)

    def hget(self, *args):
        return self.execute("HGET", *args)

    def hdel(self, *args):
        return self.execute("HDEL", *args)

    def keys(self, *args):
        return self.execute("KEYS", *args)

    def hkeys(self, *args):
        return self.execute("HKEYS", *args)

    def delete(self, *args):
        return self.execute("DEL", *args)

    def incr(self, *args):
        return self.execute("INCR", *args)

    def lpush(self, *args):
        return self.execute("LPUSH", *args)

    @property
    def client(self):
        if not self._client:
            import redis

            self._client = redis.Redis(unix_socket_path=j.core.db.connection_pool.connection_kwargs["path"], db=1)
        return self._client
