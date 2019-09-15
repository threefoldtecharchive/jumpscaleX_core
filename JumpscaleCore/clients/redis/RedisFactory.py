import time
import os

from redis._compat import nativestr

from Jumpscale import j

from Jumpscale.core.InstallTools import Redis
from Jumpscale.core.InstallTools import RedisTools


class RedisFactory(j.baseclasses.factory_testtools):

    """
    """

    __jslocation__ = "j.clients.redis"

    def _init(self, **kwargs):
        self._cache_clear()
        self._unix_socket_core = "/sandbox/var/redis.sock"
        self._core = None

        #

    @property
    def core(self):
        """
        returns the non C optimized version !
        :return:
        """
        if not self._core:
            self._core = j.clients.redis.get()
        return self._core

    def _cache_clear(self):
        """
        clear the cache formed by the functions get() and getQueue()

        """
        self._redis = {}
        self._redisq = {}
        self._config = {}

    def get(
        self,
        ipaddr="localhost",
        port=6379,
        password="",
        fromcache=True,
        unixsocket=None,
        ardb_patch=False,
        set_patch=False,
        ssl=False,
        ssl_certfile=None,
        ssl_keyfile=None,
        ssl_ca_certs=None,
        ssl_cert_reqs="required",
        timeout=10,
        ping=True,
        die=True,
        **args,
    ):
        """

        get an instance of redis client, store it in cache so we could easily retrieve it later

        :param ipaddr: used to form the key when no unixsocket, defaults to "localhost"
        :type ipaddr: str, optional
        :param port: used to form the key when no unixsocket, defaults to 6379
        :type port: int, optional
        :param password: defaults to ""
        :type password: str, optional
        :param fromcache: if False, will create a new one instead of checking cache, defaults to True
        :type fromcache: bool, optional
        :param unixsocket: path of unixsocket to be used while creating Redis, defaults to socket of the core redis
        :type unixsocket: [type], optional

        :param ssl_certfile: [description], defaults to None
        :type ssl_certfile: [type], optional
        :param ssl_keyfile: [description], defaults to None
        :type ssl_keyfile: [type], optional
        :param timeout: [description], defaults to 10
        :type timeout: int, optional
        :param ping: [description], defaults to True
        :type ping: bool, optional
        :param die: [description], defaults to True
        :type die: bool, optional

        other arguments to redis: ssl_cert_reqs=None, ssl_ca_certs=None

        set_patch is needed when using the client for gedis

        """

        if ipaddr and port:
            key = "%s_%s" % (ipaddr, port)
        else:
            unixsocket = j.core.db.connection_pool.connection_kwargs["path"]
            key = unixsocket

        if key not in self._redis or not fromcache:
            if ipaddr and port:
                self._log_debug("REDIS:%s:%s" % (ipaddr, port))
                self._redis[key] = Redis(
                    ipaddr,
                    port,
                    password=password,
                    ssl=ssl,
                    ssl_certfile=ssl_certfile,
                    ssl_keyfile=ssl_keyfile,
                    unix_socket_path=unixsocket,
                    ssl_cert_reqs=ssl_cert_reqs,
                    ssl_ca_certs=ssl_ca_certs,
                    # socket_timeout=timeout,
                    **args,
                )
            else:
                self._log_debug("REDIS:%s" % unixsocket)
                self._redis[key] = Redis(
                    unix_socket_path=unixsocket,
                    # socket_timeout=timeout,
                    password=password,
                    **args,
                )

        if ardb_patch:
            self._ardb_patch(self._redis[key])

        if set_patch:
            self._set_patch(self._redis[key])

        if ping:
            try:
                res = self._redis[key].ping()
            except Exception as e:
                if "Timeout" in str(e) or "Connection refused" in str(e):
                    if die == False:
                        return None
                    else:
                        raise j.exceptions.Base("Redis on %s:%s did not answer" % (ipaddr, port))
                else:
                    raise e

        return self._redis[key]

    def _ardb_patch(self, client):
        client.response_callbacks["HDEL"] = lambda r: r and nativestr(r) == "OK"

    def _set_patch(self, client):
        client.response_callbacks["SET"] = lambda r: r
        client.response_callbacks["DEL"] = lambda r: r

    def queue_get(self, key, redisclient=None, fromcache=True):

        if redisclient is None:
            redisclient = j.core.db

        if "host" not in redisclient.connection_pool.connection_kwargs:
            ipaddr = redisclient.connection_pool.connection_kwargs["path"]
            port = 0
        else:
            ipaddr = redisclient.connection_pool.connection_kwargs["host"]
            port = redisclient.connection_pool.connection_kwargs["port"]

        # if not fromcache:
        #     return RedisQueue(self.get(ipaddr, port, fromcache=False), name, namespace=namespace)
        key2 = "%s_%s_%s" % (ipaddr, port, key)
        if fromcache == False or key2 not in self._redisq:
            self._redisq[key2] = redisclient.queue_get(key)
        return self._redisq[key2]

    def core_get(self, reset=False, tcp=True, fromcache=True):
        """

        kosmos 'j.clients.redis.core_get(reset=False)'
        j.clients.redis.core_get(fromcache=False)

        will try to create redis connection to {DIR_TEMP}/redis.sock or /sandbox/var/redis.sock  if sandbox
        if that doesn't work then will look for std redis port
        if that does not work then will return None


        :param tcp, if True then will also start tcp port on localhost on 6379


        :param reset: stop redis, defaults to False
        :type reset: bool, optional
        :raises RuntimeError: redis couldn't be started
        :return: redis instance
        :rtype: Redis
        """
        if fromcache:
            j.core.myenv.db = RedisTools.core_get(reset=reset, tcp=tcp)
        else:
            # means we need to get a client, no need to check if core was already started
            j.core.myenv.db = RedisTools.client_core_get(fake_ok=False)
        return j.core.myenv.db

    def core_stop(self):
        """
        kill core redis

        :raises RuntimeError: redis wouldn't be stopped
        :return: True if redis is not running
        :rtype: bool
        """
        return RedisTools.core_stop()

    def core_running(self, unixsocket=True, tcp=True):

        """
        Get status of redis whether it is currently running or not

        :raises e: did not answer
        :return: True if redis is running, False if redis is not running
        :rtype: bool
        """
        return RedisTools.core_running(unixsocket=unixsocket, tcp=tcp)

    def test(self, name=""):
        """
        it's run all tests
        kosmos 'j.clients.redis.test()'

        """
        self._test_run(name=name)
