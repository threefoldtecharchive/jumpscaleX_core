import redis
import json


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
            # TODO: doesnt seem right
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

    def __init__(self, Tools, *args, **kwargs):
        self.Tools = Tools
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
            if self.Tools.cmd_installed("redis-cli_"):
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
        _, out, _ = self.Tools.execute(rediscmd, interactive=True)
        return out

    def _sp_data(self, name):
        if name not in self._storedprocedures_to_sha:
            data = self.hget("storedprocedures:data", name)
            if not data:
                raise self.Tools.exceptions.Base("could not find: '%s:%s' in redis" % (("storedprocedures:data", name)))
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
