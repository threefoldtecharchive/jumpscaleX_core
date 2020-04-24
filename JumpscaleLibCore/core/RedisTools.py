from Redis import Redis
import os
import time


class RedisTools:
    def __init__(self, myenv):
        self._tools = myenv.tools
        self._my = myenv

    def client_core_get(self, addr="localhost", port=6379, unix_socket_path="{DIR_BASE}/var/redis.sock", die=True):
        """

        :param addr:
        :param port:
        :param unix_socket_path:
        :return:
        """
        try:
            import redis
        except ImportError:
            if die:
                raise
            return

        unix_socket_path = self._tools.text_replace(unix_socket_path)
        self.unix_socket_path = unix_socket_path
        # cl = Redis(unix_socket_path=unix_socket_path, db=0)
        cl = Redis(Tools=self._tools, host=addr, port=port, db=0)
        try:
            r = cl.ping()
        except Exception as e:
            if isinstance(e, redis.exceptions.ConnectionError):
                if not die:
                    return
            raise

        assert r
        return cl

    def serialize(self, data):
        return self._tools._data_serializer_safe(data)

    def _core_get(self, reset=False, tcp=False):
        """


        will try to create redis connection to {DIR_TEMP}/redis.sock or /sandbox/var/redis.sock  if sandbox
        if that doesn't work then will look for std redis port
        if that does not work then will return None


        :param tcp, if True then will also start redis tcp port on localhost on 6379


        :param reset: stop redis, defaults to False
        :type reset: bool, optional
        :raises RuntimeError: redis couldn't be started
        :return: redis instance
        :rtype: Redis
        """

        if reset:
            self.core_stop()

        # if self._my.db and self._my.db.ping():
        #     return self._my.db

        if not self.core_running(tcp=tcp):
            self._core_start(tcp=tcp)

        db = self.client_core_get()
        return db

    def core_stop(self):
        """
        kill core redis

        :raises RuntimeError: redis wouldn't be stopped
        :return: True if redis is not running
        :rtype: bool
        """
        self._my.db = None
        self._tools.execute("redis-cli -s %s shutdown" % self.unix_socket_path, die=False, showout=False)
        self._tools.execute("redis-cli shutdown", die=False, showout=False)
        nr = 0
        while True:
            if not self.core_running():
                return True
            if nr > 200:
                raise self._tools.exceptions.Base("could not stop redis")
            time.sleep(0.05)

    def core_running(self, unixsocket=True, tcp=True):

        """
        Get status of redis whether it is currently running or not

        :raises e: did not answer
        :return: True if redis is running, False if redis is not running
        :rtype: bool
        """
        if unixsocket:
            r = self.client_core_get(die=False)
            if r:
                return True

        if tcp and self._tools.tcp_port_connection_test("localhost", 6379):
            r = self.client_core_get(addr="localhost", port=6379, die=False)
            if r:
                return True

        return False

    def _core_start(self, tcp=True, timeout=20, reset=False):

        """

        installs and starts a redis instance in separate ProcessLookupError
        when not in sandbox:
                standard on {DIR_TEMP}/redis.sock
        in sandbox will run in:
            {DIR_BASE}/var/redis.sock

        :param timeout:  defaults to 20
        :type timeout: int, optional
        :param reset: reset redis, defaults to False
        :type reset: bool, optional
        :raises RuntimeError: redis server not found after install
        :raises RuntimeError: platform not supported for start redis
        :raises self._tools.exceptions.Timeout: Couldn't start redis server
        :return: redis instance
        :rtype: Redis
        """

        if reset is False:
            if self._my.platform_is_osx:
                if not self._tools.cmd_installed("redis-server"):
                    # prefab.system.package.install('redis')
                    self._tools.execute("brew unlink redis", die=False)
                    self._tools.execute("brew install redis")
                    self._tools.execute("brew link redis")
                    if not self._tools.cmd_installed("redis-server"):
                        raise self._tools.exceptions.Base("Cannot find redis-server even after install")
                self._tools.execute("redis-cli -s {DIR_TEMP}/redis.sock shutdown", die=False, showout=False)
                self._tools.execute("redis-cli -s %s shutdown" % self.unix_socket_path, die=False, showout=False)
                self._tools.execute("redis-cli shutdown", die=False, showout=False)
            elif self._my.platform_is_linux:
                self._tools.execute("apt-get install redis-server -y")
                if not self._tools.cmd_installed("redis-server"):
                    raise self._tools.exceptions.Base("Cannot find redis-server even after install")
                self._tools.execute("redis-cli -s {DIR_TEMP}/redis.sock shutdown", die=False, showout=False)
                self._tools.execute("redis-cli -s %s shutdown" % self.unix_socket_path, die=False, showout=False)
                self._tools.execute("redis-cli shutdown", die=False, showout=False)

            else:
                raise self._tools.exceptions.Base("platform not supported for start redis")

        if not self._my.platform_is_osx:
            cmd = "sysctl vm.overcommit_memory=1"
            os.system(cmd)

        if reset:
            self.core_stop()

        cmd = (
            "mkdir -p {DIR_BASE}/var;redis-server --unixsocket $UNIXSOCKET "
            "--port 6379 "
            "--maxmemory 100000000 --daemonize yes"
        )
        cmd = cmd.replace("$UNIXSOCKET", self.unix_socket_path)
        cmd = self._tools.text_replace(cmd)

        assert "{" not in cmd

        self._tools.log(cmd)
        self._tools.execute(cmd, replace=True)
        limit_timeout = time.time() + timeout
        while time.time() < limit_timeout:
            if self.core_running():
                break
            print("trying to start redis")
            time.sleep(0.1)
        else:
            raise self._tools.exceptions.Base("Couldn't start redis server")
