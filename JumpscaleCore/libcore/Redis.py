from Tools import Tools
import redis
import json
import os
import time


class RedisQueue:
    def __init__(self, redis, key):
        self._db_ = redis
        self.key = key

    def qsize(self):
        """Return the approximate size of the queue.

        :return: approximate size of queue
        :rtype: int
        """
        return self._db_.llen(self.key)

    @property
    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def reset(self):
        """
        make empty
        :return:
        """
        while self.empty is False:
            if self.get_nowait() is None:
                self.empty = True

    def put(self, item):
        """Put item into the queue."""
        self._db_.rpush(self.key, item)

    def get(self, timeout=20):
        """Remove and return an item from the queue."""
        if timeout > 0:
            item = self._db_.blpop(self.key, timeout=timeout)
            if item:
                item = item[1]
        else:
            item = self._db_.lpop(self.key)
        return item

    def fetch(self, block=True, timeout=None):
        """Return an item from the queue without removing"""
        if block:
            # TODO: doesn not seem right
            item = self._db_.brpoplpush(self.key, self.key, timeout)
        else:
            item = self._db_.lindex(self.key, 0)
        return item

    def set_expire(self, time):
        self._db_.expire(self.key, time)

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)


class Redis(redis.Redis):

    _storedprocedures_to_sha = {}
    _redis_cli_path_ = None

    def __init__(self, *args, **kwargs):
        redis.Redis.__init__(self, *args, **kwargs)
        self._storedprocedures_to_sha = {}

    # def dict_get(self, key):
    #     return RedisDict(self, key)

    def queue_get(self, key):
        """get redis queue
        """
        return RedisQueue(self, key)

    def storedprocedure_register(self, name, nrkeys, path_or_content):
        """create stored procedure from path

        :param path: the path where the stored procedure exist
        :type path_or_content: str which is the lua content or the path
        :raises Exception: when we can not find the stored procedure on the path

        will return the sha

        to use the stored procedure do

        redisclient.evalsha(sha,3,"a","b","c")  3 is for nr of keys, then the args

        the stored procedure can be found in hset storedprocedures:$name has inside a json with

        is json encoded dict
         - script: ...
         - sha: ...
         - nrkeys: ...

        there is also storedprocedures:sha -> sha without having to decode json

        tips on lua in redis:
        https://redis.io/commands/eval

        """

        if "\n" not in path_or_content:
            f = open(path_or_content, "r")
            lua = f.read()
            path = path_or_content
        else:
            lua = path_or_content
            path = ""

        script = self.register_script(lua)

        dd = {}
        dd["sha"] = script.sha
        dd["script"] = lua
        dd["nrkeys"] = nrkeys
        dd["path"] = path

        data = json.dumps(dd)

        self.hset("storedprocedures:data", name, data)
        self.hset("storedprocedures:sha", name, script.sha)

        self._storedprocedures_to_sha = {}

        return script

    def storedprocedure_delete(self, name):
        self.hdel("storedprocedures:data", name)
        self.hdel("storedprocedures:sha", name)
        self._storedprocedures_to_sha = {}

    @property
    def _redis_cli_path(self):
        if not self.__class__._redis_cli_path_:
            if Tools.cmd_installed("redis-cli_"):
                self.__class__._redis_cli_path_ = "redis-cli_"
            else:
                self.__class__._redis_cli_path_ = "redis-cli"
        return self.__class__._redis_cli_path_

    def redis_cmd_execute(self, command, debug=False, debugsync=False, keys=None, args=None):
        """

        :param command:
        :param args:
        :return:
        """
        if not keys:
            keys = []
        if not args:
            args = []
        rediscmd = self._redis_cli_path
        if debug:
            rediscmd += " --ldb"
        elif debugsync:
            rediscmd += " --ldb-sync-mode"
        rediscmd += " --%s" % command
        for key in keys:
            rediscmd += " %s" % key
        if len(args) > 0:
            rediscmd += " , "
            for arg in args:
                rediscmd += " %s" % arg
        # print(rediscmd)
        _, out, _ = Tools.execute(rediscmd, interactive=True)
        return out

    def _sp_data(self, name):
        if name not in self._storedprocedures_to_sha:
            data = self.hget("storedprocedures:data", name)
            if not data:
                raise Tools.exceptions.Base("could not find: '%s:%s' in redis" % (("storedprocedures:data", name)))
            data2 = json.loads(data)
            self._storedprocedures_to_sha[name] = data2
        return self._storedprocedures_to_sha[name]

    def storedprocedure_execute(self, name, *args):
        """

        :param name:
        :param args:
        :return:
        """

        data = self._sp_data(name)
        sha = data["sha"]  # .encode()
        assert isinstance(sha, (str))
        # assert isinstance(sha, (bytes, bytearray))
        # Tools.shell()
        return self.evalsha(sha, data["nrkeys"], *args)
        # self.eval(data["script"],data["nrkeys"],*args)
        # return self.execute_command("EVALSHA",sha,data["nrkeys"],*args)

    def storedprocedure_debug(self, name, *args):
        """
        to see how to use the debugger see https://redis.io/topics/ldb

        to break put: redis.breakpoint() inside your lua code
        to continue: do 'c'


        :param name: name of the sp to execute
        :param args: args to it
        :return:
        """
        data = self._sp_data(name)
        path = data["path"]
        if path == "":
            from pudb import set_trace

            set_trace()

        nrkeys = data["nrkeys"]
        args2 = args[nrkeys:]
        keys = args[:nrkeys]

        out = self.redis_cmd_execute("eval %s" % path, debug=True, keys=keys, args=args2)

        return out


class RedisTools:

    _myenv = None

    @classmethod
    def myenv(cls):
        if not cls._myenv:
            from MyEnv import MyEnv

            cls._myenv = MyEnv()
        return cls._myenv

    @staticmethod
    def client_core_get(addr="localhost", port=6379, unix_socket_path="{DIR_BASE}/var/redis.sock", die=True):
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

        unix_socket_path = Tools.text_replace(unix_socket_path)
        RedisTools.unix_socket_path = unix_socket_path
        # cl = Redis(unix_socket_path=unix_socket_path, db=0)
        cl = Redis(host=addr, port=port, db=0)
        try:
            r = cl.ping()
        except Exception as e:
            if isinstance(e, redis.exceptions.ConnectionError):
                if not die:
                    return
            raise

        assert r
        return cl

    @staticmethod
    def serialize(data):
        return Tools._data_serializer_safe(data)

    @staticmethod
    def _core_get(reset=False, tcp=False):
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
            RedisTools.core_stop()

        # if myenv.db and myenv.db.ping():
        #     return myenv.db

        if not RedisTools.core_running(tcp=tcp):
            RedisTools._core_start(tcp=tcp)

        db = RedisTools.client_core_get()
        return db

    @staticmethod
    def core_stop():
        """
        kill core redis

        :raises RuntimeError: redis wouldn't be stopped
        :return: True if redis is not running
        :rtype: bool
        """
        RedisTools.myenv.db = None
        Tools.execute("redis-cli -s %s shutdown" % RedisTools.unix_socket_path, die=False, showout=False)
        Tools.execute("redis-cli shutdown", die=False, showout=False)
        nr = 0
        while True:
            if not RedisTools.core_running():
                return True
            if nr > 200:
                raise Tools.exceptions.Base("could not stop redis")
            time.sleep(0.05)

    def core_running(unixsocket=True, tcp=True):

        """
        Get status of redis whether it is currently running or not

        :raises e: did not answer
        :return: True if redis is running, False if redis is not running
        :rtype: bool
        """
        if unixsocket:
            r = RedisTools.client_core_get(die=False)
            if r:
                return True

        if tcp and Tools.tcp_port_connection_test("localhost", 6379):
            r = RedisTools.client_core_get(addr="localhost", port=6379, die=False)
            if r:
                return True

        return False

    def _core_start(tcp=True, timeout=20, reset=False):

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
        :raises Tools.exceptions.Timeout: Couldn't start redis server
        :return: redis instance
        :rtype: Redis
        """

        if reset is False:
            if RedisTools.myenv.platform_is_osx:
                if not Tools.cmd_installed("redis-server"):
                    # prefab.system.package.install('redis')
                    Tools.execute("brew unlink redis", die=False)
                    Tools.execute("brew install redis")
                    Tools.execute("brew link redis")
                    if not Tools.cmd_installed("redis-server"):
                        raise Tools.exceptions.Base("Cannot find redis-server even after install")
                Tools.execute("redis-cli -s {DIR_TEMP}/redis.sock shutdown", die=False, showout=False)
                Tools.execute("redis-cli -s %s shutdown" % RedisTools.unix_socket_path, die=False, showout=False)
                Tools.execute("redis-cli shutdown", die=False, showout=False)
            elif RedisTools.myenv.platform_is_linux:
                Tools.execute("apt-get install redis-server -y")
                if not Tools.cmd_installed("redis-server"):
                    raise Tools.exceptions.Base("Cannot find redis-server even after install")
                Tools.execute("redis-cli -s {DIR_TEMP}/redis.sock shutdown", die=False, showout=False)
                Tools.execute("redis-cli -s %s shutdown" % RedisTools.unix_socket_path, die=False, showout=False)
                Tools.execute("redis-cli shutdown", die=False, showout=False)

            else:
                raise Tools.exceptions.Base("platform not supported for start redis")

        if not myenv.platform_is_osx:
            cmd = "sysctl vm.overcommit_memory=1"
            os.system(cmd)

        if reset:
            RedisTools.core_stop()

        cmd = (
            "mkdir -p {DIR_BASE}/var;redis-server --unixsocket $UNIXSOCKET "
            "--port 6379 "
            "--maxmemory 100000000 --daemonize yes"
        )
        cmd = cmd.replace("$UNIXSOCKET", RedisTools.unix_socket_path)
        cmd = Tools.text_replace(cmd)

        assert "{" not in cmd

        Tools.log(cmd)
        Tools.execute(cmd, replace=True)
        limit_timeout = time.time() + timeout
        while time.time() < limit_timeout:
            if RedisTools.core_running():
                break
            print("trying to start redis")
            time.sleep(0.1)
        else:
            raise Tools.exceptions.Base("Couldn't start redis server")
