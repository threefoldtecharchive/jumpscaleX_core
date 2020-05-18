from __future__ import unicode_literals

import copy
import getpass
import pickle
import binascii
import bisect
import hashlib
import itertools

try:
    import msgpack
except ImportError:
    msgpack = None

try:
    import redis
except ImportError:
    redis = None

import socket
import os
import random
import shutil
import stat
import subprocess
import sys
import textwrap
import time
import re
import requests

from pathlib import Path
from subprocess import Popen
from collections import namedtuple, OrderedDict
import inspect
import json

try:
    import traceback
except ImportError:
    traceback = None

try:
    import pudb
except ImportError:
    pudb = None

try:
    import pygments
except ImportError:
    pygments = None

if pygments:
    from pygments import formatters
    from pygments import lexers

    pygments_formatter = formatters.get_formatter_by_name("terminal")
    pygments_pylexer = lexers.get_lexer_by_name("python")
else:
    pygments_formatter = False
    pygments_pylexer = False

DEFAULT_BRANCH = "master"
RepoInfo = namedtuple("RepoInfo", ["protocol", "host", "account", "name", "url", "port"])

GITHUB_RSA = "AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ=="

DEFAULT_BRANCH_WEB = "development"
GITREPOS = OrderedDict()

GITREPOS["core"] = [
    "https://github.com/threefoldtech/jumpscaleX_core",
    DEFAULT_BRANCH,
    "JumpscaleCore",
    "{DIR_BASE}/lib/jumpscale/Jumpscale",
]
GITREPOS["installer"] = [
    "https://github.com/threefoldtech/jumpscaleX_core",
    DEFAULT_BRANCH,
    "install",  # directory in the git repo
    "{DIR_BASE}/installer",
]
GITREPOS["builders"] = [
    "https://github.com/threefoldtech/jumpscaleX_builders",
    DEFAULT_BRANCH,
    "JumpscaleBuilders",
    "{DIR_BASE}/lib/jumpscale/JumpscaleBuilders",
]
GITREPOS["builders_extra"] = [
    "https://github.com/threefoldtech/jumpscaleX_builders",
    DEFAULT_BRANCH,
    "JumpscaleBuildersExtra",
    "{DIR_BASE}/lib/jumpscale/JumpscaleBuildersExtra",
]
GITREPOS["builders_builders_community"] = [
    "https://github.com/threefoldtech/jumpscaleX_builders",
    DEFAULT_BRANCH,
    "JumpscaleBuildersCommunity",
    "{DIR_BASE}/lib/jumpscale/JumpscaleBuildersCommunity",
]
GITREPOS["home"] = ["https://github.com/threefoldtech/home", "master", "", "{DIR_BASE}/lib/jumpscale/home"]
GITREPOS["libs"] = [
    "https://github.com/threefoldtech/jumpscaleX_libs",
    DEFAULT_BRANCH,
    "JumpscaleLibs",
    "{DIR_BASE}/lib/jumpscale/JumpscaleLibs",
]
GITREPOS["libs_extra"] = [
    "https://github.com/threefoldtech/jumpscaleX_libs_extra",
    DEFAULT_BRANCH,
    "JumpscaleLibsExtra",
    "{DIR_BASE}/lib/jumpscale/JumpscaleLibsExtra",
]
GITREPOS["threebot"] = [
    "https://github.com/threefoldtech/jumpscaleX_threebot",
    DEFAULT_BRANCH,
    "ThreeBotPackages",
    "{DIR_BASE}/lib/jumpscale/threebot_packages",
]
GITREPOS["weblibs"] = [
    "https://github.com/threefoldtech/jumpscaleX_weblibs",
    "%s" % DEFAULT_BRANCH_WEB,
    "static",
    "{DIR_BASE}/lib/weblibs/static",
]
GITREPOS["kosmos"] = [
    "https://github.com/threefoldtech/jumpscaleX_threebot",
    "%s" % DEFAULT_BRANCH,
    "kosmos",
    "{DIR_BASE}/lib/jumpscale/kosmos",
]

PREBUILT_REPO = ["https://github.com/threefoldtech/sandbox_threebot_linux64", "master", "", "not used"]


class BaseInstallerror(Exception):
    pass


class InputError(Exception):
    pass


try:
    import yaml

    def serializer(data):
        if isinstance(data, bytes):
            return "BINARY"
        if hasattr(data, "_ddict"):
            data = data._ddict
        try:
            data = yaml.dump(data, default_flow_style=False, default_style="", indent=4, line_break="\n")
        except Exception:
            # print("WARNING: COULD NOT YAML SERIALIZE")
            # return str(data)
            data = "CANNOT SERIALIZE YAML"
        return data


except ImportError:

    def serializer(data):
        if hasattr(data, "_data"):
            return str(data._data)
        if hasattr(data, "_ddict"):
            data = data._ddict
        try:
            return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=True)
        except Exception:
            # data = str(data)
            data = "CANNOT SERIALIZE"
            return data


def binary_search(a, x, lo=0, hi=None):  # can't use a to specify default for hi
    hi = hi if hi is not None else len(a)  # hi defaults to len(a)
    pos = bisect.bisect_left(a, x, lo, hi)  # find insertion position
    return pos if pos != hi and a[pos] == x else -1  # don't walk off the end


class RedisTools:
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
        return serializer(data)

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

        # if MyEnv.db and MyEnv.db.ping():
        #     return MyEnv.db

        if not RedisTools.core_running(tcp=tcp):
            RedisTools._core_start(tcp=tcp)

        MyEnv._db = RedisTools.client_core_get()

        try:
            from Jumpscale import j

            j.core.db = MyEnv.db
        except:
            pass

        return MyEnv.db

    @staticmethod
    def core_stop():
        """
        kill core redis

        :raises RuntimeError: redis wouldn't be stopped
        :return: True if redis is not running
        :rtype: bool
        """
        MyEnv.db = None
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
            if MyEnv.platform_is_osx:
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
            elif MyEnv.platform_is_linux:
                Tools.execute("apt-get install redis-server -y")
                if not Tools.cmd_installed("redis-server"):
                    raise Tools.exceptions.Base("Cannot find redis-server even after install")
                Tools.execute("redis-cli -s {DIR_TEMP}/redis.sock shutdown", die=False, showout=False)
                Tools.execute("redis-cli -s %s shutdown" % RedisTools.unix_socket_path, die=False, showout=False)
                Tools.execute("redis-cli shutdown", die=False, showout=False)

            else:
                raise Tools.exceptions.Base("platform not supported for start redis")

        if not MyEnv.platform_is_osx:
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


try:
    import redis
except:
    redis = False

if redis:

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


class BaseJSException(Exception):
    """
    ## log (exception) levels

        - CRITICAL 	50
        - ERROR 	40
        - WARNING 	30
        - INFO 	    20
        - STDOUT 	15
        - DEBUG 	10

    exception is the exception which comes from e.g. a try except, its to log the original exception

    e.g.

    try:
        dosomething_which_gives_error(data=data)
    except Exception as e:
        raise Tools.exceptions.Value("incredible error",cat="firebrigade.ghent",data=data,exception=e)

    :param: message a meaningful message
    :level: see above
    :cat: dot notation can be used, just to put your error in a good category
    :context: e.g. methodname, location id, ... the context (area) where the error happened (exception)
    :data: any data worth keeping


    """

    def __init__(self, message="", level=None, cat=None, msgpub=None, context=None, data=None, exception=None):

        super().__init__(message)

        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # self._exc_traceback = exc_traceback
        # self._exc_value = exc_value
        # self._exc_type = exc_type

        if level:
            if isinstance(level, str):
                level = int(level)

            elif isinstance(level, int):
                pass
            else:
                raise Tools.exceptions.JSBUG("level needs to be int or str", data=locals())
            assert level > 9
            assert level < 51

        self.message = message
        self.message_pub = msgpub
        self.level = level
        self.context = context
        self.cat = cat  # is a dot notation category, to make simple no more tags
        self.data = data
        self._logdict = None
        self.exception = exception
        self._init(message=message, level=level, cat=cat, msgpub=msgpub, context=context, exception=exception)

    def _init(self, **kwargs):
        pass

    @property
    def logdict(self):
        return self._logdict

    @property
    def type(self):
        return str(self.__class__).lower()

    @property
    def str_1_line(self):
        """
        1 line representation of exception

        """
        msg = ""
        if self.level:
            msg += "level:%s " % self.level
        msg += "type:%s " % self.type
        # if self._tags_add != "":
        #     msg += " %s " % self._tags_add
        return msg.strip()

    def __str__(self):
        if self.logdict:
            return Tools._data_serializer_safe(self.logdict)
        else:
            return self.message

    def __repr__(self):
        if not self.logdict:
            raise Tools.exceptions.JSBUG("logdict not known (is None)")
        print(Tools.log2str(self.logdict))
        return ""


class JSExceptions:
    def __init__(self):
        class Permission1(BaseJSException):
            pass

        class Halt1(BaseJSException):
            pass

        class RuntimeError1(BaseJSException):
            pass

        class Input1(BaseJSException):
            pass

        class Value1(BaseJSException):
            pass

        class NotImplemented1(BaseJSException):
            pass

        class BUG1(BaseJSException):
            pass

        class JSBUG1(BaseJSException):
            pass

        class Operations1(BaseJSException):
            pass

        class IO1(BaseJSException):
            pass

        class NotFound1(BaseJSException):
            pass

        class Timeout1(BaseJSException):
            pass

        class SSHError1(BaseJSException):
            pass

        class SSHTimeout1(BaseJSException):
            pass

        class RemoteException1(BaseJSException):
            pass

        self.Permission = Permission1
        self.SSHTimeout = SSHTimeout1
        self.SSHError = SSHError1
        self.Timeout = Timeout1
        self.NotFound = NotFound1
        self.IO = IO1
        self.Operations = Operations1
        self.JSBUG = JSBUG1
        self.BUG = BUG1
        self.NotImplemented = NotImplemented1
        self.Input = Input1
        self.Value = Value1
        self.RuntimeError = RuntimeError1
        self.Runtime = RuntimeError1
        self.Halt = Halt1
        self.Base = BaseJSException
        self.RemoteException = RemoteException1


from string import Formatter


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class OurTextFormatter(Formatter):
    def check_unused_args(self, used_args, args, kwargs):
        return used_args, args, kwargs


class LogHandler:
    def __init__(self, db, appname=None):
        self.db = db
        if appname:
            self.appname = appname
        else:
            self.appname = "init"

        self.last_logid = 0

    def _process_logdict(self, logdict):
        if "processid" not in logdict or not logdict["processid"] or logdict["processid"] == "unknown":
            logdict["processid"] = os.getpid()

        if "epoch" not in logdict or not logdict["epoch"] or logdict["epoch"] == 0:
            logdict["epoch"] = int(time.time())

        return logdict

    @property
    def rediskey_logs(self):
        return "logs:%s:data" % (self.appname)

    @property
    def rediskey_logs_incr(self):
        return "logs:%s:incr" % (self.appname)

    def handle_log(self, logdict):
        """handle error

        :param logdict: logging dict (see jumpscaleX_core/docs/Internals/logging_errorhandling/logdict.md for keys)
        :type logdict: dict
        """

        if "traceback" in logdict:
            logdict.pop("traceback")

        rediskey_logs = self.rediskey_logs
        rediskey_logs_incr = self.rediskey_logs_incr

        if not self.db:
            return

        latest_id = self.db.incr(rediskey_logs_incr)

        self.last_logid = latest_id
        logdict["id"] = latest_id

        logdict = self._process_logdict(logdict)

        data = self._dumps(logdict)

        self.db.hset(rediskey_logs, latest_id, data)

        if latest_id / 1000 >= 2 and latest_id % 1000 == 0:
            # means we need to check and maybe do some cleanup, like this we only check this every 1000 items
            # only one log handler can have this, because id's are unique because of redis
            self._data_container_dump(latest_id)

    def _dumps(self, data):
        if isinstance(data, str):
            return data
        try:
            data = json.dumps(data, ensure_ascii=False, sort_keys=False, indent=True)
            return data
        except Exception as e:
            pass
        try:
            data = str(data)
        except Exception as e:
            data = "CANNOT SERIALIZE DATA"
        return data

    def _redis_get(self, identifier, appname=None, die=True):
        """
        returns json (is the format in redis)
        :param identifier:
        :param appname:
        :param die:
        :return:
        """
        if not appname:
            appname = self.appname
        rediskey_logs = "logs:%s:data" % appname

        if not self.db:
            return
        try:
            res = self.db.hget(rediskey_logs, identifier)
        except:
            raise RuntimeError("could not find log with identifier:%s" % identifier)

        if not res:
            if die:
                raise RuntimeError("could not find log with identifier:%s" % identifier)
            return
        return res

    def _data_container_dump(self, latest_id):
        startid = latest_id - 2000
        stopid = latest_id - 1000
        # TODO, need to verify, for the next 2000 logs items we will not have them all
        if msgpack:
            r = []
            # for redis which is 1 indexed
            for i in range(startid + 1, stopid + 1):
                d = self._redis_get(i)
                r.append(d)
            assert len(r) == 1000
            log_dir = Tools.text_replace("{DIR_VAR}/logs")
            app_logs_path = "%s/%s" % (log_dir, self.appname)
            Tools.dir_ensure(app_logs_path)
            path = "%s/%s/%s.msgpack" % (log_dir, self.appname, stopid)
            Tools.file_write(path, msgpack.dumps(r))

            # rotate old msgpacks if we have logs > MAX_MSGPACKS_LOGS_COUNT (default: 50) file
            # means 50k logs, we delete the oldest 10 files, 10k logs
            msgpacks_count = MyEnv.config.get("MAX_MSGPACKS_LOGS_COUNT", 50)
            if len(os.listdir(app_logs_path)) > msgpacks_count + 1:
                all_files = sorted(Path(app_logs_path).iterdir(), key=os.path.getmtime)
                files_to_delete = all_files[: len(all_files) - msgpacks_count + 10]
                for file in files_to_delete:
                    Tools.delete(file.as_posix())

        # now remove from redis
        keystodelete = []
        for key in self.db.hkeys(self.rediskey_logs):
            if int(key) < stopid + 1:
                keystodelete.append(key)

        for chunk in chunks(keystodelete, 100):
            self.db.hdel(self.rediskey_logs, *chunk)

    def _data_container_set(self, container, appname):
        if not msgpack:
            return
        assert isinstance(container, list)
        assert len(container) == 1000
        Tools.shell()
        logdir = "%s/%s" % (self._log_dir, appname)
        if not Tools.exists(logdir):
            return []
        else:
            data = msgpack.dumps(container)
            Tools.shell()
            w


class BaseClassProperties:
    def __init__(self, **kwargs):
        self._key = None

        for key, val in kwargs.items():
            setattr(self, key, val)
        self._protected = False
        self._init(**kwargs)
        self._protected = True
        self._load()

    def _init(self, **kwargs):
        """
        this needs to be overruled
        """
        assert self._key

    def __setattr__(self, name, value):

        if name.startswith("_"):
            self.__dict__[name] = value
            return
        propobj = getattr(self.__class__, name, None)
        if isinstance(propobj, property):
            if propobj.fset is None:
                raise Tools.exceptions.Input(f"try to write protected argument on {name}")
            propobj.fset(self, value)
            return

        if not self._protected:
            if name not in self.__dict__:
                self.__dict__[name] = None
        else:
            if name not in self.__dict__:
                raise Tools.exceptions.Input(f"try to write protected argument on {name}")
        if isinstance(value, str):
            value = value.strip()
            if len(value) > 0:
                if value.startswith("'") and value.endswith("'"):
                    value = value.strip("'")
                if value.startswith('"') and value.endswith('"'):
                    value = value.strip('"')
                value = value.strip()

        if self.__dict__[name] != value:
            self.__dict__[name] = value
            self._save()

    def _load(self):
        if MyEnv.db:
            data = MyEnv.db.get(self._key)
            if data:
                data2 = json.loads(data.decode())
                self.__dict__.update(data2)

    def _save(self):
        if MyEnv.db:
            data = {}
            for key in self.__dict__.keys():
                if not key.startswith("_"):
                    data[key] = getattr(self, key)
            data2 = json.dumps(data)
            MyEnv.db.set(self._key, data2)

    def __str__(self):
        out = ""
        for key in self.__dict__.keys():
            if not key.startswith("_"):
                val = getattr(self, key)
                out += f" - {key} : {val}\n"
        return out

    __repr__ = __str__


class Tools:

    _supported_editors = ["micro", "mcedit", "joe", "vim", "vi"]  # DONT DO AS SET  OR ITS SORTED
    j = None
    _shell = None
    custom_log_printer = None

    pudb = pudb
    traceback = traceback
    pygments = pygments
    pygments_formatter = pygments_formatter
    pygments_pylexer = pygments_pylexer

    exceptions = JSExceptions()

    formatter = OurTextFormatter()
    _BaseClassProperties = BaseClassProperties

    @staticmethod
    def traceback_list_format(tb):
        """

        :param tb:
        :return: [[filepath,name,linenr,line,locals],[]]

        locals doesn't seem to be working yet, None for now

        """

        ignore_items = [
            "click/",
            "bin/kosmos",
            "ipython",
            "bpython",
            "loghandler",
            "errorhandler",
            "importlib._bootstrap",
            "gevent/",
            "gevent.",
            "__getattr__",
        ]

        def ignore(filename):
            for ignorefind in ignore_items:
                if filename.find(ignorefind) != -1:
                    return True
            return False

        if inspect.isframe(tb):
            #
            frame = tb
            res = []
            while frame:
                tb2 = inspect.getframeinfo(frame)
                if tb2.code_context:
                    if len(tb2.code_context) == 1:
                        line = tb2.code_context[0].strip()
                    else:
                        Tools.shell()
                else:
                    line = ""
                if not ignore(frame.f_code.co_filename):
                    tb_item = [frame.f_code.co_filename, frame.f_code.co_name, frame.f_lineno, line, None]
                    res.insert(0, tb_item)
                    print("++++++%s" % line)
                frame = frame.f_back
            return res

        if tb is None:
            tb = sys.last_traceback
        res = []

        for item in traceback.extract_tb(tb):
            if not ignore(item.filename):
                if item.locals:
                    Tools.shell()
                else:
                    llocals = None
                tb_item = [item.filename, item.name, item.lineno, item.line, llocals]
                res.append(tb_item)
        return res

    @staticmethod
    def get_repos_info():
        return GITREPOS

    @staticmethod
    def traceback_text_get(tb=None, stdout=False):
        """
        format traceback to readable text
        :param tb:
        :return:
        """
        if tb is None:
            tb = sys.last_traceback
        out = ""
        for item in traceback.extract_tb(tb):
            fname = item.filename
            if len(fname) > 60:
                fname = fname[-60:]
            line = "%-60s : %-4s: %s" % (fname, item.lineno, item.line)
            if stdout:
                line2 = "        {GRAY}%-60s :{RESET} %-4s: " % (fname, item.lineno)
                Tools.pprint(line2, end="", log=False)
                if Tools.pygments_formatter is not False:
                    print(
                        Tools.pygments.highlight(item.line, Tools.pygments_pylexer, Tools.pygments_formatter).rstrip()
                    )
                else:
                    Tools.pprint(item.line, log=False)

            out += "%s\n" % line
        return out

    def _traceback_filterLocals(k, v):
        try:
            k = "%s" % k
            v = "%s" % v
            if k in [
                "re",
                "q",
                "jumpscale",
                "pprint",
                "qexec",
                "jshell",
                "Shell",
                "__doc__",
                "__file__",
                "__name__",
                "__package__",
                "i",
                "main",
                "page",
            ]:
                return False
            if v.find("<module") != -1:
                return False
            if v.find("IPython") != -1:
                return False
            if v.find("bpython") != -1:
                return False
            if v.find("click") != -1:
                return False
            if v.find("<built-in function") != -1:
                return False
            if v.find("jumpscale.Shell") != -1:
                return False
        except BaseException:
            return False

        return True

    def _trace_get(self, ttype, err, tb):
        """
        #TODO: prob not used, needs to become 1 uniform way how to deal with traces
        :param ttype:
        :param err:
        :param tb:
        :return:
        """
        raise Tools.exceptions.Base()

        tblist = traceback.format_exception(ttype, err, tb)

        ignore = ["click/core.py", "ipython", "bpython", "loghandler", "errorhandler", "importlib._bootstrap"]

        # if self._limit and len(tblist) > self._limit:
        #     tblist = tblist[-self._limit:]
        tb_text = ""
        for item in tblist:
            for ignoreitem in ignore:
                if item.find(ignoreitem) != -1:
                    item = ""
            if item != "":
                tb_text += "%s" % item
        return tb_text

    def _trace_print(self, tb_text):
        if MyEnv.pygmentsObj:
            MyEnv.pygmentsObj
            # style=pygments.styles.get_style_by_name("vim")
            formatter = pygments.formatters.Terminal256Formatter()
            lexer = pygments.lexers.get_lexer_by_name("pytb", stripall=True)  # pytb
            tb_colored = pygments.highlight(tb_text, lexer, formatter)
            sys.stderr.write(tb_colored)
            # print(tb_colored)
        else:
            sys.stderr.write(tb_text)

    @staticmethod
    def log(
        msg="",
        cat=None,
        level=10,
        data=None,
        context=None,
        _levelup=0,
        tb=None,
        data_show=True,
        exception=None,
        replace=True,
        stdout=False,
        source=None,
        frame_=None,
    ):
        """

        :param msg: what you want to log
        :param cat: any dot notation category
        :param context: e.g. rack aaa in datacenter, method name in class, ...

        can use {RED}, {RESET}, ... see color codes
        :param level:
            - CRITICAL 	50
            - ERROR 	40
            - WARNING 	30
            - ENDUSER 	25
            - INFO 	    20
            - DEBUG 	10


        :param _levelup 0, if e.g. 1 means will go 1 level more back in finding line nr where log comes from
        :param source, if you don't want to show the source (line nr in log), somewhat faster
        :param stdout: return as logdict or send to stdout
        :param: replace to replace the color variables for stdout
        :param: exception is jumpscale/python exception

        :return:
        """
        logdict = {}
        if MyEnv.debug or level > 39:  # error+ is shown
            stdout = True

        if isinstance(msg, Exception):
            raise Tools.exceptions.JSBUG("msg cannot be an exception raise by means of exception=... in constructor")

        # first deal with traceback
        if exception and not tb:
            # if isinstance(exception, BaseJSException):
            if hasattr(exception, "_exc_traceback"):
                tb = exception._exc_traceback
            else:
                extype_, value_, tb = sys.exc_info()

        linenr = None
        if tb:
            logdict["traceback"] = Tools.traceback_list_format(tb)
            if len(logdict["traceback"]) > 0:
                fname, defname, linenr, line_, locals_ = logdict["traceback"][-1]

        if not linenr:
            if not frame_:
                frame_ = inspect.currentframe().f_back
                if _levelup > 0:
                    levelup = 0
                    while frame_ and levelup < _levelup:
                        frame_ = frame_.f_back
                        levelup += 1

            fname = frame_.f_code.co_filename.split("/")[-1]
            defname = frame_.f_code.co_name
            # linenr = frame_.f_code.co_firstlineno  #this is the line nr of the def
            linenr = frame_.f_lineno
            logdict["traceback"] = []

        if exception:
            # make sure exceptions get the right priority
            if isinstance(exception, Tools.exceptions.Base):
                level = exception.level

            if not level:
                level = 50

            if hasattr(exception, "exception"):
                msg_e = exception.message
            else:
                msg_e = exception.__repr__()
            if msg:
                if stdout:
                    msg = (
                        "{RED}EXCEPTION: \n"
                        + Tools.text_indent(msg, 4).rstrip()
                        + "\n"
                        + Tools.text_indent(msg_e, 4)
                        + "{RESET}"
                    )
                else:
                    msg = "EXCEPTION: \n" + Tools.text_indent(msg, 4).rstrip() + "\n" + Tools.text_indent(msg_e, 4)

            else:
                if stdout:
                    msg = "{RED}EXCEPTION: \n" + Tools.text_indent(msg_e, 4).rstrip() + "{RESET}"
                else:
                    msg = "EXCEPTION: \n" + Tools.text_indent(msg_e, 4).rstrip()
            if cat is None or cat == "":
                cat = "exception"

            if hasattr(exception, "exception"):
                if not data:
                    # copy data from the exception
                    data = exception.data
                if exception.exception:
                    # if isinstance(exception.exception, BaseJSException):
                    if hasattr(exception.exception, "exception"):
                        exception = "      " + exception.exception.str_1_line
                    else:
                        exception = Tools.text_indent(exception.exception, 6)
                    msg += "\n - original Exception: %s" % exception

        if not isinstance(msg, str):
            msg = str(msg)

        logdict["message"] = msg

        logdict["linenr"] = linenr
        logdict["filepath"] = fname
        logdict["processid"] = "unknown"  # TODO: get pid
        if source:
            logdict["source"] = source

        logdict["level"] = level
        if context:
            logdict["context"] = context
        else:
            logdict["context"] = defname

        logdict["cat"] = cat

        if data:
            if isinstance(data, dict):
                if "password" in data or "secret" in data or "passwd" in data:
                    data["password"] = "***"
            if isinstance(data, str):
                pass
            elif isinstance(data, int) or isinstance(data, str) or isinstance(data, list):
                data = str(data)
            else:
                data = Tools._data_serializer_safe(data)

        logdict["data"] = data
        if stdout:
            logdict = copy.copy(logdict)
            Tools.log2stdout(logdict, data_show=data_show)
        elif level > 14:
            Tools.log2stdout(logdict, data_show=False, enduser=True)

        iserror = tb or exception
        return Tools.process_logdict_for_handlers(logdict, iserror)

    @staticmethod
    def process_logdict_for_handlers(logdict, iserror=True):
        """

        :param logdict:
        :param iserror:   if error will use MyEnv.errorhandlers: allways MyEnv.loghandlers
        :return:
        """

        assert isinstance(logdict, dict)

        if iserror:
            for handler in MyEnv.errorhandlers:
                handler(logdict)

        else:

            for handler in MyEnv.loghandlers:
                try:
                    handler(logdict)
                except Exception as e:
                    MyEnv.exception_handle(e)

        return logdict

    @staticmethod
    def method_code_get(method, **kwargs):
        """

        :param method: the method to get the code from
        :param kwargs: will be replaced in {} template args in the method
        :return:   (methodname,code)
        """
        assert callable(method)
        code = inspect.getsource(method)
        code2 = Tools.text_strip(code)
        code3 = code2.replace("self,", "").replace("self ,", "").replace("self  ,", "")

        if kwargs:
            code3 = Tools.text_replace(code3, text_strip=False, args=kwargs)

        methodname = ""
        for line in code3.split("\n"):
            line = line.strip()
            if line.startswith("def "):
                methodname = line.split("(", 1)[0].strip().replace("def ", "")
                break

        if methodname == "":
            raise Exception("defname cannot be empty")

        return methodname, code3

    @staticmethod
    def _cmd_check(command, original_command=None):
        if not command:
            return
        if command.find("{DIR_") != -1:
            if original_command:
                print("COMMAND WAS:\n%s" % command)
                raise Tools.exceptions.Input(
                    "cannot execute found template var\ncmd:%s\n%s" % (original_command, command)
                )
            else:
                raise Tools.exceptions.Input("cannot execute found template var\ncmd:%s" % command)

    @staticmethod
    def _execute(
        command,
        async_=False,
        original_command=None,
        interactive=False,
        executor=None,
        log=True,
        retry=1,
        cwd=None,
        useShell=False,
        showout=True,
        timeout=3600,
        env=None,
        die=True,
        errormsg=None,
    ):
        if not env:
            env = {}

        if not retry:
            retry = 1

        if not executor:
            executor = MyEnv

        if executor.debug:
            showout = True

        if executor.debug or log:
            Tools.log("execute:%s" % command)
            if original_command:
                Tools.log("execute_original:%s" % original_command)

        Tools._cmd_check(command, original_command)
        rc = 1
        counter = 0
        while rc > 0 and counter < retry:
            if interactive:
                rc, out, err = Tools._execute_interactive(cmd=command)
            else:
                rc, out, err = Tools._execute_process(
                    command=command,
                    die=False,
                    env=env,
                    cwd=cwd,
                    useShell=useShell,
                    async_=async_,
                    showout=showout,
                    timeout=timeout,
                )
            if rc > 0 and retry > 1:
                Tools.log("redo cmd", level=30)
            counter += 1

        if die and rc != 0:
            if original_command:
                command = original_command
            if errormsg:
                msg = errormsg.rstrip() + "\n\n"
            else:
                msg = "\nCould not execute:"
            if command.find("\n") == -1 and len(command) < 40:
                msg += " '%s'" % command
            else:
                command = "\n".join(command.split(";"))
                msg += Tools.text_indent(command).rstrip() + "\n\n"
            if out.strip() != "":
                msg += "stdout:\n"
                msg += Tools.text_indent(out).rstrip() + "\n\n"
            if err.strip() != "":
                msg += "stderr:\n"
                msg += Tools.text_indent(err).rstrip() + "\n\n"
            raise Tools.exceptions.Base(msg)

        return rc, out, err

    @staticmethod
    def _execute_process(
        command, die=True, env=None, cwd=None, useShell=True, async_=False, showout=True, timeout=3600
    ):

        os.environ["PYTHONUNBUFFERED"] = "1"  # WHY THIS???

        # if hasattr(subprocess, "_mswindows"):
        #     mswindows = subprocess._mswindows
        # else:
        #     mswindows = subprocess.mswindows

        Tools._cmd_check(command)

        if "'" in command:
            Tools.file_write("/tmp/script_exec_process.sh", command)
            command = "sh -ex /tmp/script_exec_process.sh"

        if env is None or env == {}:
            env = os.environ

        if useShell:
            p = Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=MyEnv.platform_is_unix,
                shell=True,
                env=env,
                universal_newlines=False,
                cwd=cwd,
                bufsize=0,
                executable="/bin/bash",
            )
        else:
            args = command.split(" ")
            p = Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=MyEnv.platform_is_unix,
                shell=False,
                env=env,
                universal_newlines=False,
                cwd=cwd,
                bufsize=0,
            )

        # set the O_NONBLOCK flag of p.stdout file descriptor:
        # moving import here
        # not supported on windows
        from fcntl import F_GETFL, F_SETFL, fcntl
        from os import O_NONBLOCK

        flags = fcntl(p.stdout, F_GETFL)  # get current p.stdout flags
        flags = fcntl(p.stderr, F_GETFL)  # get current p.stderr flags
        fcntl(p.stdout, F_SETFL, flags | O_NONBLOCK)
        fcntl(p.stderr, F_SETFL, flags | O_NONBLOCK)

        out = ""
        err = ""

        if async_:
            return p

        def readout(stream):
            if MyEnv.platform_is_unix:
                # Store all intermediate data
                data = list()
                while True:
                    # Read out all available data
                    line = stream.read()
                    if not line:
                        break
                    line = line.decode()  # will be utf8
                    # Honour subprocess univeral_newlines
                    if p.universal_newlines:
                        line = p._translate_newlines(line)
                    # Add data to cache
                    data.append(line)
                    if showout:
                        Tools.pprint(line, end="")

                # Fold cache and return
                return "".join(data)

            else:
                # This is not UNIX, most likely Win32. read() seems to work
                def readout(stream):
                    line = stream.read().decode()
                    if showout:
                        # Tools.log(line)
                        Tools.pprint(line, end="")

        if timeout is None or timeout < 0:
            out, err = p.communicate()
            out = out.decode()
            err = err.decode()

        else:  # timeout set
            start = time.time()
            end = start + timeout
            now = start

            # if command already finished then read stdout, stderr
            out = readout(p.stdout)
            err = readout(p.stderr)
            if (out is None or err is None) and p.poll() is None:
                raise Tools.exceptions.Base("prob bug, needs to think this through, seen the while loop")
            while p.poll() is None:
                # means process is still running

                time.sleep(0.01)
                now = time.time()
                # print("wait")

                if timeout != 0 and now > end:
                    if MyEnv.platform_is_unix:
                        # Soft and hard kill on Unix
                        try:
                            p.terminate()
                            # Give the process some time to settle
                            time.sleep(0.2)
                            p.kill()
                            raise Tools.exceptions.Timeout(f"command: '{command}' timed out after {timeout} seconds")
                        except OSError:
                            pass
                    else:
                        # Kill on anything else
                        time.sleep(0.1)
                        if p.poll():
                            p.terminate()
                    if MyEnv.debug or showout:
                        Tools.log("process killed because of timeout", level=30)
                    return (-2, out, err)

                # Read out process streams, but don't block
                out += readout(p.stdout)
                err += readout(p.stderr)

        rc = -1 if p.returncode < 0 else p.returncode

        # close the files (otherwise resources get lost),
        # wait for the process to die, and del the Popen object
        p.stdin.close()
        p.stderr.close()
        p.stdout.close()
        p.wait()
        del p

        return (rc, out, err)

    @staticmethod
    def _execute_interactive(cmd=None):
        """
        @return returncode,stdout,sterr
        """
        # if "'" in cmd or cmd.startswith("source") or "&" in cmd:
        Tools.file_write("/tmp/script_exec_interactive.sh", cmd)
        Tools._cmd_check(cmd)
        cmd = "bash -e /tmp/script_exec_interactive.sh"
        returncode = os.system(cmd)
        # args = cmd.split(" ")
        # args[0] = shutil.which(args[0])
        # returncode = os.spawnlp(os.P_WAIT, args[0], *args)
        # cmd = " ".join(args)
        if returncode == 127:
            raise Tools.exceptions.Base("{}: command not found\n".format(cmd))
        return returncode, "", ""

    @staticmethod
    def file_touch(path):
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)

        with open(path, "a"):
            os.utime(path, None)

    @staticmethod
    def file_edit(path):
        """
        starts the editor micro with file specified
        """
        user_editor = os.environ.get("EDITOR")
        if user_editor and Tools.cmd_installed(user_editor):
            Tools._execute_interactive("%s %s" % (user_editor, path))
            return
        for editor in Tools._supported_editors:
            if Tools.cmd_installed(editor):
                Tools._execute_interactive("%s %s" % (editor, path))
                return
        raise Tools.exceptions.Base(
            "cannot edit the file: '{}', non of the supported editors is installed".format(path)
        )

    @staticmethod
    def file_write(path, content, replace=False, args=None):
        if args is None:
            args = {}
        dirname = os.path.dirname(path)
        try:
            os.makedirs(dirname, exist_ok=True)
        except FileExistsError:
            pass
        p = Path(path)
        if isinstance(content, str):
            if replace:
                content = Tools.text_replace(content, args=args)
            if MyEnv.platform_is_windows:
                with open(path, "w", newline="\n") as p:
                    p.write(content)
            else:
                p.write_text(content)
        else:
            p.write_bytes(content)

    @staticmethod
    def file_append(path, content):
        dirname = os.path.dirname(path)
        try:
            os.makedirs(dirname, exist_ok=True)
        except FileExistsError:
            pass
        my_path = Path(path)
        with my_path.open("a") as f:
            f.write(content)

    @staticmethod
    def file_text_read(path):
        path = Tools.text_replace(path)
        p = Path(path)
        try:
            return p.read_text()
        except Exception as e:
            Tools.shell()

    @staticmethod
    def file_read(path):
        path = Tools.text_replace(path)
        p = Path(path)
        try:
            return p.read_bytes()
        except Exception as e:
            Tools.shell()

    @staticmethod
    def dir_ensure(path, remove_existing=False):
        """Ensure the existance of a directory on the system, if the
        Directory does not exist, it will create

        :param path:path of the directory
        :type path: string
        :param remove_existing: If True and the path already exist,
            the existing path will be removed first, defaults to False
        :type remove_existing: bool, optional
        """

        path = Tools.text_replace(path)

        if os.path.exists(path) and remove_existing is True:
            Tools.delete(path)
        elif os.path.exists(path):
            return
        os.makedirs(path)

    @staticmethod
    def link(src, dest, chmod=None):
        """

        :param src: is where the link goes to
        :param dest: is where he link will be
        :param chmod e.g. 770
        :return:
        """
        src = Tools.text_replace(src)
        dest = Tools.text_replace(dest)
        Tools.execute("rm -f %s" % dest)
        Tools.execute("ln -s {} {}".format(src, dest))
        if chmod:
            Tools.execute("chmod %s %s" % (chmod, dest))

    @staticmethod
    def delete(path):
        """Remove a File/Dir/...
        @param path: string (File path required to be removed)
        """
        path = Tools.text_replace(path)
        if MyEnv.debug:
            Tools.log("Remove file with path: %s" % path)
        if os.path.islink(path):
            os.unlink(path)
        if not Tools.exists(path):
            return

        mode = os.stat(path).st_mode
        if os.path.isfile(path) or stat.S_ISSOCK(mode):
            if len(path) > 0 and path[-1] == os.sep:
                path = path[:-1]
            os.remove(path)
        else:
            shutil.rmtree(path)

    @staticmethod
    def path_parent(path):
        """
        Returns the parent of the path:
        /dir1/dir2/file_or_dir -> /dir1/dir2/
        /dir1/dir2/            -> /dir1/
        """
        parts = path.split(os.sep)
        if parts[-1] == "":
            parts = parts[:-1]
        parts = parts[:-1]
        if parts == [""]:
            return os.sep
        return os.sep.join(parts)

    @staticmethod
    def exists(path, followlinks=True):
        """Check if the specified path exists
        @param path: string
        @rtype: boolean (True if path refers to an existing path)
        """
        if path is None:
            raise Tools.exceptions.Value("Path is not passed in system.fs.exists")
        found = False
        try:
            st = os.lstat(path)
            found = True
        except (OSError, AttributeError):
            pass
        if found and followlinks and stat.S_ISLNK(st.st_mode):
            if MyEnv.debug:
                Tools.log("path %s exists" % str(path.encode("utf-8")))
            linkpath = os.readlink(path)
            if linkpath[0] != "/":
                linkpath = os.path.join(Tools.path_parent(path), linkpath)
            return Tools.exists(linkpath)
        if found:
            return True
        # Tools.log('path %s does not exist' % str(path.encode("utf-8")))
        return False

    @staticmethod
    def _installbase_for_shell():

        if "darwin" in MyEnv.platform():

            script = """
            pip3 install ipython==7.5.0 ptpython==2.0.4 prompt-toolkit==2.0.9 --force-reinstall
            pip3 install pudb
            pip3 install pygments
            """
            Tools.execute(script, interactive=True)

        else:

            script = """
                #if ! grep -Fq "deb http://mirror.unix-solutions.be/ubuntu/ bionic" /etc/apt/sources.list; then
                #    echo >> /etc/apt/sources.list
                #    echo "# Jumpscale Setup" >> /etc/apt/sources.list
                #    echo deb http://mirror.unix-solutions.be/ubuntu/ bionic main universe multiverse restricted >> /etc/apt/sources.list
                #fi
                sudo apt-get update
                sudo apt-get install -y python3-pip
                sudo apt-get install -y locales
                sudo apt-get install -y curl rsync
                sudo apt-get install -y unzip
                pip3 install ipython==7.5.0 ptpython==2.0.4 prompt-toolkit==2.0.9 --force-reinstall
                pip3 install pudb
                pip3 install pygments
                locale-gen --purge en_US.UTF-8
            """
            if DockerFactory.indocker():
                sudoremove = True
            else:
                sudoremove = False
            Tools.execute(script, interactive=True, sudo_remove=sudoremove)

    @staticmethod
    def get_newest_version():
        from threesdk import __version__

        # call releases api
        resp = requests.get("https://api.github.com/repos/threefoldtech/jumpscaleX_core/releases/latest")
        resp = resp.json()
        # get versions
        last_release = resp["tag_name"]
        last_release_url = resp["html_url"]
        up_to_date = True
        if last_release is not __version__:
            up_to_date = False
        return {"up_to_date": up_to_date, "last_release": last_release, "last_release_url": last_release_url}

    @staticmethod
    def clear():
        print(chr(27) + "[2j")
        print("\033c")
        print("\x1bc")

    @staticmethod
    def shell(loc=True):

        if loc:
            import inspect

            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            f = calframe[1]
        else:
            f = None
        if Tools._shell is None:

            try:
                from IPython.terminal.embed import InteractiveShellEmbed
            except Exception as e:
                print("NEED TO INSTALL BASICS FOR DEBUG SHELL SUPPORT")
                Tools._installbase_for_shell()
                from IPython.terminal.embed import InteractiveShellEmbed
            if f:
                print("\n*** file: %s" % f.filename)
                print("*** function: %s [linenr:%s]\n" % (f.function, f.lineno))

            Tools._shell = InteractiveShellEmbed(banner1="", exit_msg="")
            Tools._shell.Completer.use_jedi = False

        return Tools._shell(stack_depth=2)

    # @staticmethod
    # def shell(loc=True,exit=True):
    #     if loc:
    #         import inspect
    #         curframe = inspect.currentframe()
    #         calframe = inspect.getouterframes(curframe, 2)
    #         f = calframe[1]
    #         print("\n*** file: %s"%f.filename)
    #         print("*** function: %s [linenr:%s]\n" % (f.function,f.lineno))
    #     from ptpython.repl import embed
    #     Tools.clear()
    #     history_filename="~/.jsx_history"
    #     if not Tools.exists(history_filename):
    #         Tools.file_write(history_filename,"")
    #     ptconfig = None
    #     if exit:
    #         sys.exit(embed(globals(), locals(),configure=ptconfig,history_filename=history_filename))
    #     else:
    #         embed(globals(), locals(),configure=ptconfig,history_filename=history_filename)

    @staticmethod
    def text_strip(
        content, ignorecomments=False, args={}, replace=False, executor=None, colors=False, die_if_args_left=False
    ):
        """
        remove all spaces at beginning & end of line when relevant (this to allow easy definition of scripts)
        args will be substitued to .format(...) string function https://docs.python.org/3/library/string.html#formatspec
        MyEnv.config will also be given to the format function


        for examples see text_replace method


        """
        # find generic prepend for full file
        minchars = 9999
        prechars = 0
        assert isinstance(content, str)
        for line in content.split("\n"):
            if line.strip() == "":
                continue
            if ignorecomments:
                if line.strip().startswith("#") and not line.strip().startswith("#!"):
                    continue
            prechars = len(line) - len(line.lstrip())
            # print("'%s':%s:%s" % (line, prechars, minchars))
            if prechars < minchars:
                minchars = prechars

        if minchars > 0:

            # if first line is empty, remove
            lines = content.split("\n")
            if len(lines) > 0:
                if lines[0].strip() == "":
                    lines.pop(0)
            content = "\n".join(lines)

            # remove the prechars
            content = "\n".join([line[minchars:] for line in content.split("\n")])

        if replace:
            content = Tools.text_replace(
                content=content, args=args, executor=executor, text_strip=False, die_if_args_left=die_if_args_left
            )
        else:
            if colors and "{" in content:
                for key, val in MyEnv.MYCOLORS.items():
                    content = content.replace("{%s}" % key, val)

        return content

    @staticmethod
    def bool(txt):
        if not txt:
            return False
        txt = str(txt).lower().strip()
        if txt in ["true", "1", "yes"]:
            return True
        return False

    @staticmethod
    def text_strip_to_ascii_dense(text):
        """
        convert to ascii converting as much as possibe to ascii
        replace -,:... to _
        lower the text
        remove all the other parts

        """
        # text = unidecode(text)  # convert to ascii letters
        # text=self.strip_to_ascii(text) #happens later already
        text = text.lower()
        text = text.replace("\n", "")
        text = text.replace("\t", "")
        text = text.replace(" ", "")

        def replace(char):
            if char in "-/\\= ;!+()":
                return "_"
            return char

        def check(char):
            charnr = ord(char)
            if char in "._":
                return True
            if charnr > 47 and charnr < 58:
                return True
            if charnr > 96 and charnr < 123:
                return True
            return False

        res = [replace(char) for char in str(text)]
        res = [char for char in res if check(char)]
        text = "".join(res)
        while "__" in text:
            text = text.replace("__", "_")
        text = text.rstrip("_")
        return text

    @staticmethod
    def text_replace(
        content,
        args=None,
        executor=None,
        ignorecomments=False,
        text_strip=True,
        die_if_args_left=False,
        ignorecolors=False,
        primitives_only=False,
    ):
        """

        Tools.text_replace

        content example:

        "{name!s:>10} {val} {n:<10.2f}"  #floating point rounded to 2 decimals
        format as in str.format_map() function from

        following colors will be replaced e.g. use {RED} to get red color.

        MYCOLORS =
                "RED",
                "BLUE",
                "CYAN",
                "GREEN",
                "YELLOW,
                "RESET",
                "BOLD",
                "REVERSE"

        """

        if isinstance(content, bytes):
            content = content.decode()

        if not isinstance(content, str):
            raise Tools.exceptions.Input("content needs to be str")

        if args is None:
            args = {}

        if not "{" in content:
            return content

        if executor:
            content2 = Tools.args_replace(
                content,
                # , executor.info.cfg_jumpscale
                args_list=(args, executor.config),
                ignorecolors=ignorecolors,
                die_if_args_left=die_if_args_left,
                primitives_only=primitives_only,
            )
        else:
            content2 = Tools.args_replace(
                content,
                args_list=(args, MyEnv.config),
                ignorecolors=ignorecolors,
                die_if_args_left=die_if_args_left,
                primitives_only=primitives_only,
            )

        if text_strip:
            content2 = Tools.text_strip(content2, ignorecomments=ignorecomments, replace=False)

        return content2

    @staticmethod
    def args_replace(content, args_list=None, primitives_only=False, ignorecolors=False, die_if_args_left=False):
        """

        :param content:
        :param args: add all dicts you want to replace in a list
        :return:
        """

        # IF YOU TOUCH THIS LET KRISTOF KNOW (despiegk)

        assert isinstance(content, str)
        assert args_list

        if content == "":
            return content

        def arg_process(key, val):
            if key in ["self"]:
                return None
            if val is None:
                return ""
            if isinstance(val, str):
                if val.strip().lower() == "none":
                    return None
                return val
            if isinstance(val, bool):
                if val:
                    return "1"
                else:
                    return "0"
            if isinstance(val, int) or isinstance(val, float):
                return val
            if isinstance(val, list) or isinstance(val, set):
                out = "["
                for v in val:
                    if isinstance(v, str):
                        v = "'%s'" % v
                    else:
                        v = str(v)
                    out += "%s," % v
                val = out.rstrip(",") + "]"
                return val
            if primitives_only:
                return None
            else:
                return Tools._data_serializer_safe(val)

        def args_combine():
            args_new = {}
            for replace_args in args_list:
                for key, val in replace_args.items():
                    if key not in args_new:
                        val = arg_process(key, val)
                        if val:
                            args_new[key] = val

            for field_name in MyEnv.MYCOLORS:
                if ignorecolors:
                    args_new[field_name] = ""
                else:
                    args_new[field_name] = MyEnv.MYCOLORS[field_name]

            return args_new

        def process_line_failback(line):
            args_new = args_combine()
            # SLOW!!!
            # print("FALLBACK REPLACE:%s" % line)
            for arg, val in args_new.items():
                assert arg
                line = line.replace("{%s}" % arg, str(val))
            return line

        def process_line(line):
            if line.find("{") == -1:
                return line
            emptyone = False
            if line.find("{}") != -1:
                emptyone = True
                line = line.replace("{}", ">>EMPTYDICT<<")

            try:
                items = [i for i in Tools.formatter.parse(line)]
            except Exception as e:
                return process_line_failback(line)

            do = {}

            for literal_text, field_name, format_spec, conversion in items:
                if not field_name:
                    continue
                if field_name in MyEnv.MYCOLORS:
                    if ignorecolors:
                        do[field_name] = ""
                    else:
                        do[field_name] = MyEnv.MYCOLORS[field_name]
                for args in args_list:
                    if field_name in args:
                        do[field_name] = arg_process(field_name, args[field_name])
                if field_name not in do:
                    if die_if_args_left:
                        raise Tools.exceptions.Input("could not find:%s in line:%s" % (field_name, line))
                    # put back the original
                    if conversion and format_spec:
                        do[field_name] = "{%s!%s:%s}" % (field_name, conversion, format_spec)
                    elif format_spec:
                        do[field_name] = "{%s:%s}" % (field_name, format_spec)
                    elif conversion:
                        do[field_name] = "{%s!%s}" % (field_name, conversion)
                    else:
                        do[field_name] = "{%s}" % (field_name)

            try:
                line = line.format_map(do)
            except KeyError as e:
                # means the format map did not work,lets fall back on something more failsafe
                return process_line_failback(line)
            except ValueError as e:
                # means the format map did not work,lets fall back on something more failsafe
                return process_line_failback(line)
            except Exception as e:
                return line
            if emptyone:
                line = line.replace(">>EMPTYDICT<<", "{}")

            return line

        out = ""
        for line in content.split("\n"):
            if "{" in line:
                line = process_line(line)
            out += "%s\n" % line

        out = out[:-1]  # needs to remove the last one, is because of the split there is no last \n
        return out

    @staticmethod
    def _data_serializer_safe(data):
        if isinstance(data, dict):
            data = data.copy()  # important to have a shallow copy of data so we don't change original
            for key in ["passwd", "password", "secret"]:
                if key in data:
                    data[key] = "***"
        elif isinstance(data, int) or isinstance(data, str) or isinstance(data, list):
            return str(data)

        serialized = serializer(data)
        res = Tools.text_replace(content=serialized, ignorecolors=True)
        return res

    @staticmethod
    def log2stdout(logdict, data_show=False, enduser=False):
        def show():
            # always show in debugmode and critical
            if MyEnv.debug or (logdict and logdict["level"] >= 50):
                return True
            if not MyEnv.log_console:
                return False
            return logdict and (logdict["level"] >= MyEnv.log_level)

        if not show() and not data_show:
            return

        if enduser:
            if "public" in logdict and logdict["public"]:
                msg = logdict["public"]
            else:
                msg = logdict["message"]
            if logdict["level"] > 29:
                print(Tools.text_replace("{RED} * %s{RESET}\n" % msg))
            else:
                print(Tools.text_replace("{YELLOW} * %s{RESET}\n" % msg))
            return

        text = Tools.log2str(logdict, data_show=True, replace=True)
        p = print
        if MyEnv.config.get("LOGGER_PANEL_NRLINES"):
            if Tools.custom_log_printer:
                p = Tools.custom_log_printer
        try:
            p(text)
        except UnicodeEncodeError as e:
            text = text.encode("ascii", "ignore")
            p(text)

    @staticmethod
    def traceback_format(tb, replace=True):
        """format traceback

        :param tb: traceback
        :type tb: traceback object or a formatted list
        :return: formatted trackeback
        :rtype: str
        """
        if not isinstance(tb, list):
            tb = Tools.traceback_list_format(tb)

        out = Tools.text_replace("\n{RED}--TRACEBACK------------------{RESET}\n")
        for tb_path, tb_name, tb_lnr, tb_line, tb_locals in tb:
            C = "{GREEN}{tb_path}{RESET} in {BLUE}{tb_name}{RESET}\n"
            C += "    {GREEN}{tb_lnr}{RESET}    {tb_code}{RESET}"
            if Tools.pygments_formatter:
                tb_code = Tools.pygments.highlight(tb_line, Tools.pygments_pylexer, Tools.pygments_formatter).rstrip()
            else:
                tb_code = tb_line
            tbdict = {"tb_path": tb_path, "tb_name": tb_name, "tb_lnr": tb_lnr, "tb_code": tb_code}
            C = Tools.text_replace(C.lstrip(), args=tbdict, text_strip=True)
            out += C.rstrip() + "\n"
        out += Tools.text_replace("{RED}-----------------------------\n{RESET}")
        return out

    @staticmethod
    def log2str(logdict, data_show=True, replace=True):
        """

        :param logdict:

            logdict["linenr"]
            logdict["processid"]
            logdict["message"]
            logdict["filepath"]
            logdict["level"]
            logdict["context"]
            logdict["cat"]
            logdict["data"]
            logdict["epoch"]
            logdict["traceback"]

        :return:
        """

        if "epoch" in logdict:
            timetuple = time.localtime(logdict["epoch"])
        else:
            timetuple = time.localtime(time.time())
        logdict["TIME"] = time.strftime(MyEnv.FORMAT_TIME, timetuple)

        if logdict["level"] < 11:
            LOGLEVEL = "DEBUG"
        elif logdict["level"] == 15:
            LOGLEVEL = "STDOUT"
        elif logdict["level"] < 21:
            LOGLEVEL = "INFO"
        elif logdict["level"] < 31:
            LOGLEVEL = "WARNING"
        elif logdict["level"] < 41:
            LOGLEVEL = "ERROR"
        else:
            LOGLEVEL = "CRITICAL"

        LOGFORMAT = MyEnv.LOGFORMAT[LOGLEVEL]

        if len(logdict["filepath"]) > 20:
            logdict["filename"] = logdict["filepath"][-20:]
        else:
            logdict["filename"] = logdict["filepath"]

        if len(logdict["context"]) > 35:
            logdict["context"] = logdict["context"][len(logdict["context"]) - 34 :]
        # if logdict["context"].startswith("_"):
        #     logdict["context"] = ""
        # elif logdict["context"].startswith(":"):
        #     logdict["context"] = ""

        out = ""

        # TO SHOW WERE LOG COMES FROM e.g. from subprocess
        if "source" in logdict:
            out += Tools.text_replace("{RED}--SOURCE: %s-20--{RESET}\n" % logdict["source"])

        msg = Tools.text_replace(LOGFORMAT, args=logdict, die_if_args_left=False).rstrip()
        out += msg

        if "traceback" in logdict and logdict["traceback"]:
            out += Tools.traceback_format(logdict["traceback"])

        if data_show:
            if logdict["data"] != None:
                if isinstance(logdict["data"], dict):
                    try:
                        data = serializer(logdict["data"])
                    except Exception as e:
                        data = logdict["data"]
                else:
                    data = logdict["data"]
                data = Tools.text_indent(data, 2, strip=True)
                out += Tools.text_replace("\n{YELLOW}--DATA-----------------------\n")
                out += data.rstrip() + "\n"
                out += Tools.text_replace("-----------------------------{RESET}\n")

        if logdict["level"] > 39:
            # means is error
            if "public" in logdict and logdict["public"]:
                out += (
                    "{YELLOW}" + Tools.text_indent(logdict["public"].rstrip(), nspaces=2, prefix="* ") + "{RESET}\n\n"
                )

        # restore the logdict
        logdict.pop("TIME")
        logdict.pop("filename")

        if replace:
            out = Tools.text_replace(out)
            if out.find("{RESET}") != -1:
                Tools.shell()

        return out

    @staticmethod
    def pprint(content, ignorecomments=False, text_strip=False, args=None, colors=True, indent=0, end="\n", log=True):
        """

        :param content: what to print
        :param ignorecomments: ignore #... on line
        :param text_strip: remove spaces at start of line
        :param args: replace args {} is template construct
        :param colors:
        :param indent:


        MYCOLORS =
                "RED",
                "BLUE",
                "CYAN",
                "GREEN",
                "RESET",
                "BOLD",
                "REVERSE"

        """
        if not isinstance(content, str):
            content = str(content)
        if args or colors or text_strip:
            content = Tools.text_replace(
                content, args=args, text_strip=text_strip, ignorecomments=ignorecomments, die_if_args_left=False
            )
            for key, val in MyEnv.MYCOLORS.items():
                content = content.replace("{%s}" % key, val)
        elif content.find("{RESET}") != -1:
            for key, val in MyEnv.MYCOLORS.items():
                content = content.replace("{%s}" % key, val)

        if indent > 0:
            content = Tools.text_indent(content)
        if log:
            Tools.log(content, level=15, stdout=False)

        try:
            print(content, end=end)
        except UnicodeEncodeError as e:
            content = content.encode("ascii", "ignore")
            print(content)

    @staticmethod
    def text_md5(txt):
        import hashlib

        if isinstance(s, str):
            s = s.encode("utf-8")
        impl = hashlib.new("md5", data=s)
        return impl.hexdigest()

    @staticmethod
    def text_indent(content, nspaces=4, wrap=120, strip=True, indentchar=" ", prefix=None, args=None):
        """Indent a string a given number of spaces.

        Parameters
        ----------

        instr : basestring
            The string to be indented.
        nspaces : int (default: 4)
            The number of spaces to be indented.

        Returns
        -------

        str|unicode : string indented by ntabs and nspaces.

        """
        if content is None:
            raise Tools.exceptions.Base("content cannot be None")
        if content == "":
            return content
        if not prefix:
            prefix = ""
        content = str(content)
        if args is not None:
            content = Tools.text_replace(content, args=args)
        if strip:
            content = Tools.text_strip(content, replace=False)
        if wrap > 0:
            content = Tools.text_wrap(content, wrap)

            # flatten = True
        ind = indentchar * nspaces
        out = ""
        for line in content.split("\n"):
            if line.strip() == "":
                out += "\n"
            else:
                out += "%s%s%s\n" % (ind, prefix, line)
        if content[-1] == "\n":
            out = out[:-1]
        return out

    @staticmethod
    def text_wrap(txt, length=120):
        out = ""
        for line in txt.split("\n"):
            out += textwrap.fill(line, length, subsequent_indent="    ") + "\n"
        return out

    @staticmethod
    def _file_path_tmp_get(ext="sh"):
        ext = ext.strip(".")
        if MyEnv.platform_is_windows:
            Tools.dir_ensure(Tools.text_replace("{DIR_BASE}\\tmp"))
            return Tools.text_replace("{DIR_BASE}\\tmp\\{RANDOM}.{ext}", args={"RANDOM": Tools._random(), "ext": ext})
        return Tools.text_replace("/tmp/jumpscale/scripts/{RANDOM}.{ext}", args={"RANDOM": Tools._random(), "ext": ext})

    @staticmethod
    def _random():
        return str(random.getrandbits(16))

    def get_envars(self):
        envars = dict()
        content = self.file_read("/proc/1/environ").strip("\x00").split("\x00")
        for item in content:
            k, v = item.split("=")
            envars[k] = v
        return envars

    @staticmethod
    def execute_jumpscale(cmd, die=True):
        Tools.execute(cmd, jumpscale=True, die=die)

    @staticmethod
    def _script_process_jumpscale(script, env={}, debug=False, interactive=None):
        pre = ""

        if "from Jumpscale import j" not in script:
            # now only do if multicommands
            pre += "from Jumpscale import j\n"

        if interactive:
            pre += "j.application.interactive=True\n"

        if debug:
            pre += "j.application.debug = True\n"  # TODO: is this correct

        if pre:
            script = "%s\n%s" % (pre, script)

        script = Tools._script_process_python(script, env=env)

        return script

    @staticmethod
    def _script_process_python(script, env={}):
        pre = ""

        if env != {}:
            for key, val in env.items():
                pre += "%s = %s\n" % (key, val)

        if pre:
            script = "%s\n%s" % (pre, script)

        return script

    @staticmethod
    def _script_process_bash(script, die=True, env={}, sudo=False, debug=False):

        pre = ""

        if die:
            # first make sure not already one
            if "set -e" not in script:
                if debug:
                    pre += "set -ex\n"
                else:
                    pre += "set -e\n"

        if env != {}:
            for key, val in env.items():
                pre += "export %s=%s\n" % (key, val)

        if pre:
            script = "%s\n%s" % (pre, script)

        # if sudo:
        #     script = self.sudo_cmd(script)

        return script

    @staticmethod
    def _cmd_process(
        cmd,
        python=None,
        jumpscale=None,
        die=True,
        env={},
        sudo=None,
        debug=False,
        replace=False,
        executor=None,
        interactive=None,
    ):
        """
        if file then will read
        if \n in cmd then will treat as script
        if script will upload as file

        :param cmd:
        :param interactive: means we will run as interactive in a shell, for python always the case

        :return:
        """

        cmd = Tools.text_strip(cmd)

        assert sudo is None or sudo is False  # not implemented yet
        if env is None:
            env = {}

        if Tools.exists(cmd):
            ext = os.path.splitext(cmd)[1].lower()
            cmd = Tools.file_read(cmd)
            if python is None and jumpscale is None:
                if ext == ".py":
                    python = True

        script = None

        if "\n" in cmd or python or jumpscale or "'" in cmd:
            script = cmd

        dest = None
        if script:
            if executor:
                name = executor.name
            else:
                name = str(random.randint(1, 1000))
            if python or jumpscale:
                dest = "/tmp/script_%s.py" % name

                if jumpscale:
                    script = Tools._script_process_jumpscale(
                        script=script, env=env, debug=debug, interactive=interactive
                    )
                    cmd = "source {DIR_BASE}/env.sh && python3 %s" % dest
                else:
                    script = Tools._script_process_python(script, env=env)
                    cmd = "source {DIR_BASE}/env.sh && python3 %s" % dest
            else:
                dest = "/tmp/script_%s.sh" % name
                if die:
                    cmd = "bash -e %s" % dest
                else:
                    cmd = "bash %s" % dest
                script = Tools._script_process_bash(script, die=die, env=env, debug=debug)

            if replace:
                script = Tools.text_replace(script, args=env, executor=executor)
            if executor:
                executor.file_write(dest, script)
            else:
                Tools.file_write(dest, script)

            # if MyEnv.debug:
            #     Tools.log(script)

        if replace:
            cmd = Tools.text_replace(cmd, args=env, executor=executor)

        Tools._cmd_check(cmd)
        Tools._cmd_check(script)

        return dest, cmd

    @staticmethod
    def execute(
        command,
        showout=True,
        cwd=None,
        timeout=3600,
        die=True,
        async_=False,
        args=None,
        interactive=False,
        replace=True,
        original_command=None,
        log=False,
        sudo_remove=False,
        retry=None,
        errormsg=None,
        die_if_args_left=False,
        jumpscale=False,
        python=False,
        executor=None,
        debug=False,
        useShell=True,
    ):

        # windows only
        if MyEnv.platform_is_windows:
            if replace:
                command = Tools.text_replace(command, args=args).rstrip("\n").replace("\n", "&&")
            if interactive:
                subprocess.call(command, shell=True)
                return
            else:
                res = Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=useShell)
                out = res.communicate()[0].decode()
                rc = res.wait()
                if rc > 0 and die:
                    raise Tools.exceptions.RuntimeError(f"Error in executing {command}: Traceback:\n{out}")
                return rc, out, None

        if callable(command):
            method_name, command = Tools.method_code_get(command, **args)
            command += "%s()" % method_name
            jumpscale = True

        env = {}
        if args:
            env.update(args)

        if not retry:
            retry = 1
        if not original_command:
            original_command = command + ""  # to have copy

        if sudo_remove:
            command = command.replace("sudo ", "")

        tempfile, command = Tools._cmd_process(
            command,
            python=python,
            jumpscale=jumpscale,
            die=die,
            env=env,
            sudo=False,
            debug=debug,
            replace=replace,
            executor=executor,
            interactive=interactive,
        )

        if die_if_args_left and "{" in command:
            raise Tools.exceptions.Input("Found { in %s" % command)

        r = Tools._execute(
            command,
            async_=async_,
            original_command=original_command,
            interactive=interactive,
            executor=executor,
            log=log,
            retry=retry,
            cwd=cwd,
            useShell=useShell,
            showout=showout,
            timeout=timeout,
            env=env,
            die=die,
            errormsg=errormsg,
        )
        if tempfile:
            Tools.delete(tempfile)
        return r

    @staticmethod
    def system_cleanup():
        print("- AM CLEANING UP THE CONTAINER, THIS TAKES A WHILE")
        CMD = BaseInstaller.cleanup_script_get()
        for line in CMD.split("\n"):
            Tools.execute(line, replace=False)

    @staticmethod
    def process_pids_get_by_filter(filterstr, excludes=[], current_user=False):
        allflag = "" if current_user else "a"
        cmd = f"ps {allflag}x | grep '{filterstr}'"
        rcode, out, err = Tools.execute(cmd, showout=False)
        # print out
        found = []

        def checkexclude(c, excludes):
            for item in excludes:
                c = c.lower()
                if c.find(item.lower()) != -1:
                    return True
            return False

        for line in out.split("\n"):
            if line.find("grep") != -1 or line.strip() == "":
                continue
            if line.strip() != "":
                if line.find(filterstr) != -1:
                    line = line.strip()
                    if not checkexclude(line, excludes):
                        # print "found pidline:%s"%line
                        found.append(int(line.split(" ")[0]))
        return found

    @staticmethod
    def process_kill_by_pid(pid):
        Tools.execute("kill -9 %s" % pid)

    @staticmethod
    def process_kill_by_by_filter(filterstr, current_user=False):
        for pid in Tools.process_pids_get_by_filter(filterstr, current_user=current_user):
            Tools.process_kill_by_pid(pid)

    @staticmethod
    def ask_choices(msg, choices=[], default=None):
        Tools._check_interactive()
        msg = Tools.text_strip(msg)
        print(msg)
        if "\n" in msg:
            print()
        choices = [str(i) for i in choices if i not in [None, "", ","]]
        choices_txt = ",".join(choices)
        mychoice = input("make your choice (%s): " % choices_txt)
        while mychoice not in choices:
            if mychoice.strip() == "" and default:
                return default
            print("ERROR: only choose %s please" % choices_txt)
            mychoice = input("make your choice (%s): " % choices_txt)
        return mychoice

    @staticmethod
    def ask_yes_no(msg, default="y"):
        """

        :param msg: the msg to show when asking for y or no
        :return: will return True if yes
        """
        Tools._check_interactive()
        return Tools.ask_choices(msg, "y,n", default=default) in ["y", ""]

    @staticmethod
    def _check_interactive():
        if not MyEnv.interactive:
            raise Tools.exceptions.Base("Cannot use console in a non interactive mode.")

    @staticmethod
    def ask_password(question="give secret", confirm=True, regex=None, retry=-1, validate=None, emptyok=False):
        """Present a password input question to the user

        @param question: Password prompt message
        @param confirm: Ask to confirm the password
        @type confirm: bool
        @param regex: Regex to match in the response
        @param retry: Integer counter to retry ask for respone on the question
        @param validate: Function to validate provided value

        @returns: Password provided by the user
        @rtype: string
        """
        Tools._check_interactive()

        import getpass

        startquestion = question
        if question.endswith(": "):
            question = question[:-2]
        question += ": "
        value = None
        failed = True
        retryCount = retry
        while retryCount != 0:
            response = getpass.getpass(question)
            if emptyok and not response:
                return ""
            if (not regex or re.match(regex, response)) and (not validate or validate(response)):
                if value == response or not confirm:
                    return response
                elif not value:
                    failed = False
                    value = response
                    question = "%s (confirm): " % (startquestion)
                else:
                    value = None
                    failed = True
                    question = "%s: " % (startquestion)
            if failed:
                print("Invalid password!")
                retryCount = retryCount - 1
        raise Tools.exceptions.Base(
            "Console.askPassword() failed: tried %s times but user didn't fill out a value that matches '%s'."
            % (retry, regex)
        )

    @staticmethod
    def ask_string(msg, default=None):
        Tools._check_interactive()
        msg = Tools.text_strip(msg)
        print(msg)
        if "\n" in msg:
            print()
        txt = input()
        if default and txt.strip() == "":
            txt = default
        return txt

    @staticmethod
    def cmd_installed(name):
        if not name in MyEnv._cmd_installed:
            MyEnv._cmd_installed[name] = shutil.which(name) != None
        return MyEnv._cmd_installed[name]

    @staticmethod
    def cmd_args_get():
        res = {}
        for i in sys.argv[1:]:
            if "=" in i:
                name, val = i.split("=", 1)
                name = name.strip("-").strip().strip("-")
                val = val.strip().strip("'").strip('"').strip()
                res[name.lower()] = val
            elif i.strip() != "":
                name = i.strip("-").strip().strip("-")
                res[name.lower()] = True
        return res

    @staticmethod
    def tcp_port_connection_test(ipaddr, port, timeout=None):
        start = time.time()

        def check():
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if timeout:
                    conn.settimeout(timeout)
                try:
                    conn.connect((ipaddr, port))
                except BaseException:
                    return False
            finally:
                if conn:
                    conn.close()
            return True

        if timeout and timeout > 0:
            while time.time() < start + timeout:
                if check():
                    return True
            return False
        else:
            return check()

    @staticmethod
    def _code_location_get(account, repo, executor=None):
        """
        accountdir will be created if it does not exist yet
        :param repo:
        :param static: static means we don't use git

        :return: repodir_exists,foundgit, accountdir,repodir

            foundgit means, we found .git in the repodir
            dontpull means, we found .dontpull in the repodir, means code is being synced to the repo from remote, should not update

        """

        prefix = "code"
        if executor and not isinstance(executor, ExecutorLocal):
            accountdir = f"/sandbox/code/github/{account}"
        elif "DIR_CODE" in MyEnv.config:
            accountdir = os.path.join(MyEnv.config["DIR_CODE"], "github", account)
        else:
            accountdir = os.path.join(MyEnv.config["DIR_BASE"], prefix, "github", account)

        executor = executor or ExecutorLocal()

        repodir = os.path.join(accountdir, repo)
        gitdir = os.path.join(repodir, ".git")
        dontpullloc = os.path.join(repodir, ".dontpull")
        if executor.exists(accountdir):
            if executor.find(accountdir) == []:
                executor.delete(accountdir)  # lets remove the dir & return it does not exist

        exists = executor.exists(repodir)
        foundgit = executor.exists(gitdir)
        dontpull = executor.exists(dontpullloc)
        return exists, foundgit, dontpull, accountdir, repodir

    @staticmethod
    def code_changed(path):
        """
        check if there is code in there which changed
        :param path:
        :return:
        """

        S = "git -C {REPO_DIR} diff --exit-code && git -C {REPO_DIR} diff --cached --exit-code"
        args = {}
        args["REPO_DIR"] = path
        rc, out, err = Tools.execute(S, showout=False, die=False, args=args)
        return rc > 0

    @staticmethod
    def code_github_use_ssh():
        """
        Will check if we can use ssh to clone/pull our repos
        """
        Tools.known_hosts_update("github.com", key=f"github.com ssh-rsa {GITHUB_RSA}")
        repoinfo = Tools.code_git_rewrite_url(GITREPOS["core"][0], ssh=True)
        rc, _, _, = Tools.execute(f"git ls-remote --tags {repoinfo.url}", die=False, interactive=False, showout=False)
        return rc == 0

    @staticmethod
    def known_hosts_update(host, port=22, key=None):
        if key is None:
            cmd = f"ssh-keyscan -t rsa -p {port} {host}"
            _, key, _ = Tools.execute(cmd, showout=False)
        if MyEnv.platform_is_windows:
            known_host_path = r"%s\.ssh\known_hosts" % MyEnv._homedir_get()
        else:
            known_host_path = "%s/.ssh/known_hosts" % MyEnv.config["DIR_HOME"]
        # ensure parent directory
        Tools.dir_ensure(os.path.dirname(known_host_path))
        haskey = False
        if os.path.exists(known_host_path):
            with open(known_host_path) as fd:
                for line in fd:
                    if key in line:
                        haskey = True
                        break
        if not haskey:
            with open(known_host_path, "a+") as fd:
                fd.write(key.strip() + "\n")

    @staticmethod
    def code_git_rewrite_url(url="", login=None, passwd=None, ssh="auto"):
        """
        Rewrite the url of a git repo with login and passwd if specified

        Args:
            url (str): the HTTP URL of the Git repository. ex: 'https://github.com/despiegk/odoo'
            login (str): authentication login name
            passwd (str): authentication login password
            ssh = if True will build ssh url, if "auto" or "first" will check if there is ssh-agent available & keys are loaded,
                if yes will use ssh (True)
                if no will use http (False)

        Returns:
            (repository_host, repository_type, repository_account, repository_name, repository_url, port)
        """

        url = url.strip()
        if ssh == "auto" or ssh == "first":
            try:
                ssh = MyEnv.available
            except:
                ssh = False
        elif ssh or ssh is False:
            pass
        else:
            raise Tools.exceptions.Base("ssh needs to be auto, first or True or False: here:'%s'" % ssh)

        if url.startswith("ssh://"):
            url = url.replace("ssh://", "")

        port = None
        if ssh:
            login = "ssh"
            try:
                port = int(url.split(":")[1].split("/")[0])
                url = url.replace(":%s/" % (port), ":")
            except BaseException:
                pass

        url_pattern_ssh = re.compile("^(git@)(.*?):(.*?)/(.*?)/?$")
        sshmatch = url_pattern_ssh.match(url)
        url_pattern_ssh2 = re.compile("^(git@)(.*?)/(.*?)/(.*?)/?$")
        sshmatch2 = url_pattern_ssh2.match(url)
        url_pattern_http = re.compile("^(https?://)(.*?)/(.*?)/(.*?)/?$")
        httpmatch = url_pattern_http.match(url)
        if sshmatch:
            match = sshmatch
            url_ssh = True
        elif sshmatch2:
            match = sshmatch2
            url_ssh = True
        elif httpmatch:
            match = httpmatch
            url_ssh = False
        else:
            raise Tools.exceptions.Base(
                "Url is invalid. Must be in the form of 'http(s)://hostname/account/repo' or 'git@hostname:account/repo'\nnow:\n%s"
                % url
            )

        protocol, repository_host, repository_account, repository_name = match.groups()
        assert repository_name.strip() != ""
        assert repository_account.strip() != ""

        if protocol.startswith("git") and ssh is False:
            protocol = "https://"

        if not repository_name.endswith(".git"):
            repository_name += ".git"

        if (login == "ssh" or url_ssh) and ssh:
            if port is None:
                repository_url = "ssh://git@%(host)s/%(account)s/%(name)s" % {
                    "host": repository_host,
                    "account": repository_account,
                    "name": repository_name,
                }
            else:
                repository_url = "ssh://git@%(host)s:%(port)s/%(account)s/%(name)s" % {
                    "host": repository_host,
                    "port": port,
                    "account": repository_account,
                    "name": repository_name,
                }
            protocol = "ssh"

        elif login and login != "guest":
            repository_url = "%(protocol)s%(login)s:%(password)s@%(host)s/%(account)s/%(repo)s" % {
                "protocol": protocol,
                "login": login,
                "password": passwd,
                "host": repository_host,
                "account": repository_account,
                "repo": repository_name,
            }

        else:
            repository_url = "%(protocol)s%(host)s/%(account)s/%(repo)s" % {
                "protocol": protocol,
                "host": repository_host,
                "account": repository_account,
                "repo": repository_name,
            }
        if repository_name.endswith(".git"):
            repository_name = repository_name[:-4]

        return RepoInfo(protocol, repository_host, repository_account, repository_name, repository_url, port)

    @staticmethod
    def code_gitrepo_args(url="", dest=None, login=None, passwd=None, reset=False, ssh="auto"):
        """
        Extracts and returns data useful in cloning a Git repository.

        Args:
            url (str): the HTTP/GIT URL of the Git repository to clone from. eg: 'https://github.com/odoo/odoo.git'
            dest (str): the local filesystem path to clone to
            login (str): authentication login name (only for http)
            passwd (str): authentication login password (only for http)
            reset (boolean): if True, any cached clone of the Git repository will be removed
            branch (str): branch to be used
            ssh if auto will check if ssh-agent loaded, if True will be forced to use ssh for git

        # Process for finding authentication credentials (NOT IMPLEMENTED YET)

        - first check there is an ssh-agent and there is a key attached to it, if yes then no login & passwd will be used & method will always be git
        - if not ssh-agent found
            - then we will check if url is github & ENV argument GITHUBUSER & GITHUBPASSWD is set
                - if env arguments set, we will use those & ignore login/passwd arguments
            - we will check if login/passwd specified in URL, if yes willl use those (so they get priority on login/passwd arguments)
            - we will see if login/passwd specified as arguments, if yes will use those
        - if we don't know login or passwd yet then
            - login/passwd will be fetched from local git repo directory (if it exists and reset==False)
        - if at this point still no login/passwd then we will try to build url with anonymous


        Returns:
            (repository_host, repository_type, repository_account, repository_name, dest, repository_url)

            - repository_type http or git

        Remark:
            url can be empty, then the git params will be fetched out of the git configuration at that path
        """
        url = url.strip()
        if url == "":
            if dest is None:
                raise Tools.exceptions.Base("dest cannot be None (url is also '')")
            if not Tools.exists(dest):
                raise Tools.exceptions.Base(
                    "Could not find git repo path:%s, url was not specified so git destination needs to be specified."
                    % (dest)
                )

        if login is None and url.find("github.com/") != -1:
            # can see if there if login & passwd in OS env
            # if yes fill it in
            if "GITHUBUSER" in os.environ:
                login = os.environ["GITHUBUSER"]
            if "GITHUBPASSWD" in os.environ:
                passwd = os.environ["GITHUBPASSWD"]

        (
            protocol,
            repository_host,
            repository_account,
            repository_name,
            repository_url,
            port,
        ) = Tools.code_git_rewrite_url(url=url, login=login, passwd=passwd, ssh=ssh)

        repository_type = repository_host.split(".")[0] if "." in repository_host else repository_host

        codeDir = MyEnv.config["DIR_CODE"]

        if not dest:
            dest = "%(codedir)s/%(type)s/%(account)s/%(repo_name)s" % {
                "codedir": codeDir,
                "type": repository_type.lower(),
                "account": repository_account.lower(),
                "repo_name": repository_name,
            }

        if reset:
            Tools.delete(dest)

        return repository_host, repository_type, repository_account, repository_name, dest, repository_url, port

    @staticmethod
    def code_giturl_parse(url):
        """
        @return (repository_host, repository_type, repository_account, repository_name, repository_url,branch,gitpath, relpath,repository_port)

        example Input
        - https://github.com/threefoldtech/jumpscale_/NOS/blob/master/specs/NOS_1.0.0.md
        - https://github.com/threefoldtech/jumpscale_/jumpscaleX_core/blob/8.1.2/lib/Jumpscale/tools/docsite/macros/dot.py
        - https://github.com/threefoldtech/jumpscale_/jumpscaleX_core/tree/8.2.0/lib/Jumpscale/tools/docsite/macros
        - https://github.com/threefoldtech/jumpscale_/jumpscaleX_core/tree/master/lib/Jumpscale/tools/docsite/macros

        :return
        - repository_account e,g, threefoldtech
        - repository_name is the name e.g. jumpscale_ in this case
        - repository_type e.g. github
        - repository_url the full url to the repo but rewritten
        - gitpath the path to the location on the filesystem for after checkout with the part inside the git repo
        - relpath: path inside the git repo


        """
        url = url.strip()
        (
            repository_host,
            repository_type,
            repository_account,
            repository_name,
            repository_url,
            port,
        ) = Tools.code_git_rewrite_url(url=url)
        url_end = ""
        if "tree" in repository_url:
            # means is a directory
            repository_url, url_end = repository_url.split("tree")
        elif "blob" in repository_url:
            # means is a directory
            repository_url, url_end = repository_url.split("blob")
        if url_end != "":
            url_end = url_end.strip("/")
            if url_end.find("/") == -1:
                path = ""
                branch = url_end
                if branch.endswith(".git"):
                    branch = branch[:-4]
            else:
                branch, path = url_end.split("/", 1)
                if path.endswith(".git"):
                    path = path[:-4]
        else:
            path = ""
            branch = ""

        a, b, c, d, dest, e, port = Tools.code_gitrepo_args(url)

        if "tree" in dest:
            # means is a directory
            gitpath, ee = dest.split("tree")
        elif "blob" in dest:
            # means is a directory
            gitpath, ee = dest.split("blob")
        else:
            gitpath = dest

        return (
            repository_host,
            repository_type,
            repository_account,
            repository_name,
            repository_url,
            branch,
            gitpath,
            path,
            port,
        )

    @staticmethod
    def code_github_get(url, rpath=None, branch=None, pull=False, reset=False, executor=None, shallow=False):
        """

        :param repo:
        :param account:
        :param branch: falls back to the default branch on MyEnv.DEFAULT_BRANCH
                    if needed, when directory exists and pull is False will not check branch
        :param pull:
        :param reset:
        :return:
        """
        executor = executor or ExecutorLocal()

        def getbranch(args):
            cmd = "git -C {REPO_DIR} rev-parse --abbrev-ref HEAD"
            rc, stdout, err = executor.execute(cmd, die=False, args=args, showout=False, interactive=False)
            if rc > 0:
                Tools.shell()
            current_branch = stdout.strip()
            Tools.log("Found branch: %s" % current_branch)
            return current_branch

        def checkoutbranch(args, branch):
            args["BRANCH"] = branch
            current_branch = getbranch(args=args)
            if current_branch != branch:
                script = "git -C {REPODIR} checkout -q -f {BRANCH}"
                if Tools.ask_yes_no(
                    f"\n**: A different branch ({current_branch}) found in repo ({repo}), do you want to change it to ({branch})?"
                ):
                    rc, out, err = executor.execute(script, die=False, args=args, showout=False, interactive=True)
                else:
                    raise Tools.exceptions.Input(f"Cannot continue please change repo ({repo}) to branch to ({branch})")

                if rc > 0:
                    return False

            return True

        def reset_changes(args):
            C = """
            cd {REPO_DIR}
            git checkout -q . --force
            """
            Tools.log(f"get code & ignore changes: {args['NAME']}")
            executor.execute(
                C, args=args, retry=1, errormsg=f"Could not checkout {url}", interactive=True,
            )

        def assert_merge(args):
            C = """
            cd {REPO_DIR}
            git pull -q {URL}
            """
            rc, out, err = executor.execute(
                C, args=args, retry=1, errormsg=f"Couldn't merge repo {args['URL']}", interactive=True,
            )
            return rc == 0

        (host, type, account, repo, url2, branch2, gitpath, path, port) = Tools.code_giturl_parse(url=url)
        if rpath:
            path = rpath
        assert "/" not in repo

        if branch is None:
            branch = branch2
        elif isinstance(branch, str):
            if "," in branch:
                raise Tools.exceptions.JSBUG("no support for multiple branches yet")
                branch = [branch.strip() for branch in branch.split(",")]
        elif isinstance(branch, (set, list)):
            raise Tools.exceptions.JSBUG("no support for multiple branches yet")
            branch = [branch.strip() for branch in branch]
        else:
            raise Tools.exceptions.JSBUG("branch should be a string or list, now %s" % branch)

        Tools.log("get code:%s:%s (%s)" % (url, path, branch))

        exists, foundgit, dontpull, ACCOUNT_DIR, REPO_DIR = Tools._code_location_get(
            account=account, repo=repo, executor=executor
        )

        args = {}
        args["ACCOUNT_DIR"] = ACCOUNT_DIR
        args["REPO_DIR"] = REPO_DIR
        args["URL"] = url
        args["NAME"] = repo
        if "SSH_AUTH_SOCK" in os.environ:
            args["SSH_AUTH_SOCK"] = os.environ["SSH_AUTH_SOCK"]

        args["BRANCH"] = branch  # TODO:no support for multiple branches yet

        if exists and shallow:
            if getbranch(args) != branch:
                Tools.delete(REPO_DIR)
                exists = False
                foundgit = False

        if "GITPULL" in os.environ:
            pull = str(os.environ["GITPULL"]) == "1"

        git_on_system = executor.cmd_installed("git")

        if exists and not foundgit and not pull:
            """means code is already there, maybe synced?"""
            return gitpath
        if exists and not foundgit and pull:
            raise Tools.exceptions.Input(
                f"Can not pull repo {REPO_DIR} because .git folder is missing, please clean the repo and try again"
            )

        if git_on_system and MyEnv.config["USEGIT"]:
            # there is ssh-key loaded
            # or there is a dir with .git inside and exists
            # or it does not exist yet
            # then we need to use git

            C = ""

            if exists is False:
                try:
                    Tools.log("get code [git] (first time): %s" % repo)
                    if not executor.exists(ACCOUNT_DIR):
                        executor.dir_ensure(ACCOUNT_DIR)
                    C = "git -C {ACCOUNT_DIR} clone {URL} -b {BRANCH} -q"
                    if shallow:
                        C += " --depth=1"
                    executor.execute(
                        C,
                        args=args,
                        die=True,
                        showout=True,
                        interactive=True,
                        retry=4,
                        errormsg=f"Could not clone {url}",
                    )

                except Exception:
                    Tools.log("get code [https] (default branch): %s" % repo)
                    C = "git -C {ACCOUNT_DIR} clone -q {URL}"
                    if shallow:
                        C += " --depth=1"
                    executor.execute(
                        C,
                        args=args,
                        die=True,
                        showout=True,
                        interactive=True,
                        retry=4,
                        errormsg=f"Could not clone {url}",
                    )
            else:
                if pull:
                    if reset:
                        reset_changes(args)
                    else:
                        if Tools.code_changed(REPO_DIR):
                            if Tools.ask_yes_no(
                                "\n**:found changes in repo '%s', do you want to reset?\n WARNING: This will delete all local changes"
                                % repo
                            ):
                                reset_changes(args)
                            else:
                                if Tools.ask_yes_no(
                                    "\n**: you chose not to reset in repo '%s', do you want to commit?" % repo
                                ):
                                    if "GITMESSAGE" in os.environ:
                                        args["MESSAGE"] = os.environ["GITMESSAGE"]
                                    else:
                                        args["MESSAGE"] = input("\nprovide commit message: ")
                                        assert args["MESSAGE"].strip() != ""
                                    if assert_merge(args):
                                        C = """
                                           cd {REPO_DIR}
                                           git add . -A
                                           git commit -m "{MESSAGE}"
                                           """
                                        Tools.log("get code & commit [git]: %s" % repo)
                                        executor.execute(C, args=args, interactive=True)
                                    else:
                                        raise Tools.exceptions.Input(
                                            "you have uncommitted changes, automatic pull failed, please resolve and update before continuing"
                                        )
                                else:
                                    raise Tools.exceptions.Input("found changes, do not want to commit or reset")
                    # update repo
                    cmd = "git -C {REPO_DIR} fetch -q {URL}"
                    if shallow:
                        cmd += " --depth=1"
                    executor.execute(
                        cmd,
                        args=args,
                        retry=4,
                        showout=False,
                        errormsg=f"Could not fetch {url}",
                        interactive=True,
                    )
                    # switch branch
                    if not checkoutbranch(args, branch):
                        raise Tools.exceptions.Input("Could not checkout branch:%s on %s" % (branch, args["REPO_DIR"]))
                    Tools.log("update code: %s" % repo)
                    executor.execute(
                        "git -C {REPO_DIR} rebase -q origin/{BRANCH}",
                        args=args,
                        retry=4,
                        showout=False,
                        errormsg=f"Could not pull {url}",
                        interactive=True,
                    )

        else:
            Tools.log("get code [zip]: %s" % repo)
            args = {}
            args["ACCOUNT_DIR"] = ACCOUNT_DIR
            args["REPO_DIR"] = REPO_DIR
            args["URL"] = "https://github.com/%s/%s/archive/%s.zip" % (account, repo, branch)
            args["NAME"] = repo
            args["BRANCH"] = branch.strip()

            script = """
            set -e
            cd {DIR_TEMP}
            rm -f download.zip
            curl -L {URL} > download.zip
            """
            executor.execute(script, args=args, retry=3, errormsg="Cannot download:%s" % args["URL"])
            statinfo = os.stat("/tmp/jumpscale/download.zip")
            if statinfo.st_size < 100000:
                raise Tools.exceptions.Operations("cannot download:%s resulting file was too small" % args["URL"])
            else:
                script = """
                set -e
                cd {DIR_TEMP}
                rm -rf {NAME}-{BRANCH}
                mkdir -p {REPO_DIR}
                rm -rf {REPO_DIR}
                unzip download.zip > /tmp/unzip
                mv {NAME}-{BRANCH} {REPO_DIR}
                rm -f download.zip
                """
                try:
                    executor.execute(script, args=args, die=True, interactive=True)
                except Exception:
                    Tools.shell()

        return gitpath

    @staticmethod
    def config_load(path="", if_not_exist_create=False, executor=None, content="", keys_lower=False):
        """
        only 1 level deep toml format only for int,string,bool
        no multiline support for text fields

        :param: keys_lower if True will lower the keys

        return dict

        """
        path = Tools.text_replace(path)
        res = {}
        if content == "":
            if executor is None:
                if os.path.exists(path):
                    t = Tools.file_text_read(path)
                else:
                    if if_not_exist_create:
                        Tools.config_save(path, {})
                    return {}
            else:
                if executor.exists(path):
                    t = executor.file_read(path)
                else:
                    if if_not_exist_create:
                        Tools.config_save(path, {}, executor=executor)
                    return {}
        else:
            t = content

        for line in t.split("\n"):
            if line.strip() == "":
                continue
            if line.startswith("#"):
                continue
            if "=" not in line:
                raise Tools.exceptions.Input("Cannot process config: did not find = in line '%s'" % line)
            key, val = line.split("=", 1)
            if "#" in val:
                val = val.split("#", 1)[0]
            key = key.strip().upper()
            val = val.strip().strip("'").strip().strip('"').strip()
            if str(val).lower() in [0, "false", "n", "no"]:
                val = False
            elif str(val).lower() in [1, "true", "y", "yes"]:
                val = True
            elif str(val).find("[") != -1:
                val2 = str(val).strip("[").strip("]")
                val = [
                    item.strip().strip("'").strip().strip('"').strip() for item in val2.split(",") if item.strip() != ""
                ]
            else:
                try:
                    val = int(val)
                except:
                    pass
            if keys_lower:
                key = key.lower()
            res[key] = val

        return res

    @staticmethod
    def config_save(path, data, upper=True, executor=None):
        path = Tools.text_replace(path)
        out = ""
        for key, val in data.items():
            if upper:
                key = key.upper()
            if isinstance(val, list):
                val2 = "["
                for item in val:
                    val2 += "'%s'," % item
                val2 = val2.rstrip(",")
                val2 += "]"
                val = val2
            elif isinstance(val, str):
                val = "'%s'" % val
            elif isinstance(val, int) or isinstance(val, float):
                val = str(val)
            elif val is True:
                val = "true"
            elif val is False:
                val = "false"
            out += "%s = %s\n" % (key, val)

        if executor:
            executor.file_write(path, out)
        else:
            Tools.file_write(path, out)

    @staticmethod
    def to_mnemonic(data, english):
        if len(data) not in [16, 20, 24, 28, 32]:
            raise Tools.exceptions.Value(
                "Data length should be one of the following: [16, 20, 24, 28, 32], but it is not (%d)." % len(data)
            )
        h = hashlib.sha256(data).hexdigest()
        b = (
            bin(int(binascii.hexlify(data), 16))[2:].zfill(len(data) * 8)
            + bin(int(h, 16))[2:].zfill(256)[: len(data) * 8 // 32]
        )
        result = []
        for i in range(len(b) // 11):
            idx = int(b[i * 11 : (i + 1) * 11], 2)
            result.append(english[idx])
        result_phrase = " ".join(result)
        return result_phrase

    @staticmethod
    def to_entropy(words, english):
        if not isinstance(words, list):
            words = words.split(" ")
        if len(words) not in [12, 15, 18, 21, 24]:
            raise Tools.exceptions.Value(
                "Number of words must be one of the following: [12, 15, 18, 21, 24], but it is not (%d)." % len(words)
            )
        # Look up all the words in the list and construct the
        # concatenation of the original entropy and the checksum.
        concatLenBits = len(words) * 11
        concatBits = [False] * concatLenBits
        wordindex = 0
        use_binary_search = True
        for word in words:
            # Find the words index in the wordlist
            ndx = binary_search(english, word) if use_binary_search else english.index(word)
            if ndx < 0:
                raise Tools.exceptions.NotFound('Unable to find "%s" in word list.' % word)
            # Set the next 11 bits to the value of the index.
            for ii in range(11):
                concatBits[(wordindex * 11) + ii] = (ndx & (1 << (10 - ii))) != 0
            wordindex += 1
        checksumLengthBits = concatLenBits // 33
        entropyLengthBits = concatLenBits - checksumLengthBits
        # Extract original entropy as bytes.
        entropy = bytearray(entropyLengthBits // 8)
        for ii in range(len(entropy)):
            for jj in range(8):
                if concatBits[(ii * 8) + jj]:
                    entropy[ii] |= 1 << (7 - jj)
        # Take the digest of the entropy.
        hashBytes = hashlib.sha256(entropy).digest()
        hashBits = list(itertools.chain.from_iterable(([c & (1 << (7 - i)) != 0 for i in range(8)] for c in hashBytes)))
        # Check all the checksum bits.
        for i in range(checksumLengthBits):
            if concatBits[entropyLengthBits + i] != hashBits[i]:
                raise Tools.exceptions.Value("Failed checksum.")
        return bytes(entropy)


class MyEnv_:
    def __init__(self):
        """

        :param configdir: default /sandbox/cfg, then ~/sandbox/cfg if not exists
        :return:
        """
        self.DEFAULT_BRANCH = DEFAULT_BRANCH
        self.readonly = False  # if readonly will not manipulate local filesystem appart from /tmp
        self.sandbox_python_active = False  # means we have a sandboxed environment where python3 works in
        self.sandbox_lua_active = False  # same for lua
        self.config_changed = False
        self._cmd_installed = {}
        # should be the only location where we allow logs to be going elsewhere
        self.loghandlers = []
        self.errorhandlers = []
        self.state = None
        self.__init = False
        self.debug = False
        self.log_console = False
        self.log_level = 15
        self._secret = None

        self.sshagent = None
        self.interactive = False

        self.appname = "installer"

        self.FORMAT_TIME = "%a %d %H:%M:%S"

        self.MYCOLORS = {
            "RED": "\033[1;31m",
            "BLUE": "\033[1;34m",
            "CYAN": "\033[1;36m",
            "GREEN": "\033[0;32m",
            "GRAY": "\033[0;37m",
            "YELLOW": "\033[0;33m",
            "RESET": "\033[0;0m",
            "BOLD": "\033[;1m",
            "REVERSE": "\033[;7m",
        }

        self.MYCOLORS_IGNORE = {
            "RED": "",
            "BLUE": "",
            "CYAN": "",
            "GREEN": "",
            "GRAY": "",
            "YELLOW": "",
            "RESET": "",
            "BOLD": "",
            "REVERSE": "",
        }

        LOGFORMATBASE = "{COLOR}{TIME} {filename:<20}{RESET} -{linenr:4d} - {GRAY}{context:<35}{RESET}: {message}"  # DO NOT CHANGE COLOR

        self.LOGFORMAT = {
            "DEBUG": LOGFORMATBASE.replace("{COLOR}", "{CYAN}"),
            "STDOUT": "{message}",
            # 'INFO': '{BLUE}* {message}{RESET}',
            "INFO": LOGFORMATBASE.replace("{COLOR}", "{BLUE}"),
            "WARNING": LOGFORMATBASE.replace("{COLOR}", "{YELLOW}"),
            "ERROR": LOGFORMATBASE.replace("{COLOR}", "{RED}"),
            "CRITICAL": "{RED}{TIME} {filename:<20} -{linenr:4d} - {GRAY}{context:<35}{RESET}: {message}",
        }
        self._db = None

    @property
    def db(self):
        if self._db == "NOTUSED":
            return None
        if not self._db:
            if RedisTools.client_core_get(die=False):
                self._db = RedisTools._core_get()
            else:
                self._db = "NOTUSED"
                return

        return self._db

    def redis_start(self):
        self._db = RedisTools._core_get()

    def secret_set(self, secret=None, secret_expiration_hours=48):
        """
        can be the hash or the originating secret passphrase

        """
        if not secret:
            secret = Tools.ask_password("please provide passphrase (to locally encrypt your container)")
            assert len(secret) < 32

        secret = self._secret_format(secret)

        expiration = secret_expiration_hours * 3600

        if MyEnv.db:
            self.db.set("threebot.secret.encrypted", secret, ex=expiration)

        return secret

    def _secret_format(self, secret):

        if not isinstance(secret, bytes):
            secret = secret.encode()

        if len(secret) != 32:
            import hashlib

            m = hashlib.md5(secret)
            secret = m.hexdigest()

        return secret

    def secret_get(self):
        if not self._secret:
            secret = None

            # toremove = None
            # for key in sys.argv:
            #     if key.startswith("--secret"):
            #         secret = key.split("=", 1)[1].strip()
            #         # start the redis, because secret specified
            #         RedisTools._core_get()
            #         MyEnv.secret_set(secret=secret)
            #         toremove = key
            #
            # if toremove:
            #     # means we can remove the --secret from sys.arg
            #     # important to do or future command line arg parsing will fail
            #     sys.argv.pop(sys.argv.index(toremove))

            if MyEnv.db:
                secret = self.db.get("threebot.secret.encrypted")

            if "JSXSECRET" in os.environ:
                secret = os.environ["JSXSECRET"].strip()
                secret = self._secret_format(secret)

            if not secret:
                secret = self.secret_set()

            if isinstance(secret, bytes):
                secret = secret.decode()

            self._secret = secret

            assert len(self._secret) == 32

        return self._secret

    def init(self):
        if self.__init:
            return

        if self.platform() == "linux":
            self.platform_is_linux = True
            self.platform_is_unix = True
            self.platform_is_osx = False
            self.platform_is_windows = False
        elif "darwin" in self.platform():
            self.platform_is_linux = False
            self.platform_is_unix = True
            self.platform_is_osx = True
            self.platform_is_windows = False
        elif "win32" in self.platform():
            self.platform_is_linux = False
            self.platform_is_unix = False
            self.platform_is_osx = False
            self.platform_is_windows = True
        else:
            raise Tools.exceptions.Base("platform not supported, only linux, osx and windows.")

        configdir = self._cfgdir_get()
        basedir = self._basedir_get()

        if basedir == "/sandbox" and not os.path.exists(basedir):
            script = """
            set -e
            cd /
            sudo mkdir -p /sandbox/cfg
            sudo chown -R {USERNAME}:{GROUPNAME} /sandbox
            mkdir -p /usr/local/EGG-INFO
            sudo chown -R {USERNAME}:{GROUPNAME} /usr/local/EGG-INFO
            """
            args = {}
            args["USERNAME"] = getpass.getuser()
            st = os.stat(self.config["DIR_HOME"])
            gid = st.st_gid
            # import is here cause it's only unix
            # for windows support
            import grp

            args["GROUPNAME"] = grp.getgrgid(gid)[0]
            Tools.execute(script, interactive=True, args=args, die_if_args_left=True)

        # Set codedir
        Tools.dir_ensure(f"{basedir}/code")
        self.config_file_path = os.path.join(configdir, "jumpscale_config.toml")
        self.state_file_path = os.path.join(configdir, "jumpscale_done.toml")

        if Tools.exists(self.config_file_path):
            self._config_load()
            if not "DIR_BASE" in self.config:
                return
        else:
            self.config = self.config_default_get()

        self.log_includes = [i for i in self.config.get("LOGGER_INCLUDE", []) if i.strip().strip("''") != ""]
        self.log_excludes = [i for i in self.config.get("LOGGER_EXCLUDE", []) if i.strip().strip("''") != ""]
        self.log_level = self.config.get("LOGGER_LEVEL", 10)
        # self.log_console = self.config.get("LOGGER_CONSOLE", False)
        # self.log_redis = self.config.get("LOGGER_REDIS", True)
        self.debug = self.config.get("DEBUG", False)
        if "JSXDEBUG" in os.environ:
            self.debug = True
        self.debugger = self.config.get("DEBUGGER", "pudb")

        if os.path.exists(os.path.join(self.config["DIR_BASE"], "bin", "python3.6")):
            self.sandbox_python_active = True
        else:
            self.sandbox_python_active = False

        self._state_load()

        self.sshagent = SSHAgent()

        sys.excepthook = self.excepthook
        if redis and Tools.exists("{}/bin".format(self.config["DIR_BASE"])):  # To check that Js is on host
            self.loghandler_redis = LogHandler(db=self.db)
        else:
            # print("- redis loghandler cannot be loaded")
            self.loghandler_redis = None

        self.__init = True

    def platform(self):
        """
        will return one of following strings:
            linux, darwin

        """
        return sys.platform

    #
    # def platform_is_linux(self):
    #     return "posix" in sys.builtin_module_names

    def check_platform(self):
        """check if current platform is supported (linux or darwin)
        for linux, the version check is done by `UbuntuInstaller.ensure_version()`

        :raises RuntimeError: in case platform is not supported
        """
        platform = self.platform()
        if "linux" in platform:
            UbuntuInstaller.ensure_version()
        elif "darwin" not in platform:
            raise Tools.exceptions.Base("Your platform is not supported")

    def _homedir_get(self):
        if self.platform_is_windows:
            return os.environ["USERPROFILE"]
        if "HOMEDIR" in os.environ:
            dir_home = os.environ["HOMEDIR"]
        elif "HOME" in os.environ:
            dir_home = os.environ["HOME"]
        else:
            dir_home = "/root"
        return dir_home

    def _basedir_get(self):
        if self.readonly:
            return "/tmp/jumpscale"

        if "linux" in self.platform():
            isroot = None
            rc, out, err = Tools.execute("whoami", showout=False, die=False)
            if rc == 0:
                if out.strip() == "root":
                    isroot = 1
            if Tools.exists("/sandbox") or isroot == 1:
                Tools.dir_ensure("/sandbox")
                return "/sandbox"
        if self.platform_is_windows:
            p = "%s\sandbox" % self._homedir_get()
        else:
            p = "%s/sandbox" % self._homedir_get()
        if not Tools.exists(p):
            Tools.dir_ensure(p)
        return p

    def _cfgdir_get(self):
        if self.readonly:
            return "/tmp/jumpscale/cfg"
        return "%s/cfg" % self._basedir_get() if not MyEnv.platform_is_windows else "%s\cfg" % self._basedir_get()

    def _identitydir_get(self):
        return f"{self._basedir_get()}/myhost" if not MyEnv.platform_is_windows else "%s\myhost" % self._basedir_get()

    def _codedir_get(self):
        return f"{self._basedir_get()}/code" if not MyEnv.platform_is_windows else "%s\code" % self._basedir_get()

    def config_default_get(self, config={}):
        if "DIR_BASE" not in config:
            config["DIR_BASE"] = self._basedir_get()

        if "DIR_HOME" not in config:
            config["DIR_HOME"] = self._homedir_get()

        if not "DIR_CFG" in config:
            config["DIR_CFG"] = self._cfgdir_get()

        if not "DIR_IDENTITY" in config:
            config["DIR_IDENTITY"] = self._identitydir_get()

        if not "READONLY" in config:
            config["READONLY"] = False
        if not "DEBUG" in config:
            config["DEBUG"] = False
        if not "DEBUGGER" in config:
            config["DEBUGGER"] = "pudb"
        if "LOGGER_INCLUDE" not in config:
            config["LOGGER_INCLUDE"] = ["*"]
        if "LOGGER_EXCLUDE" not in config:
            config["LOGGER_EXCLUDE"] = ["sal.fs"]
        if "LOGGER_LEVEL" not in config:
            config["LOGGER_LEVEL"] = 15  # means std out & plus gets logged
        if config["LOGGER_LEVEL"] > 50:
            config["LOGGER_LEVEL"] = 50
        # if "LOGGER_CONSOLE" not in config:
        #     config["LOGGER_CONSOLE"] = True
        # if "LOGGER_REDIS" not in config:
        #     config["LOGGER_REDIS"] = False
        if "LOGGER_PANEL_NRLINES" not in config:
            config["LOGGER_PANEL_NRLINES"] = 0

        if self.readonly:
            config["DIR_TEMP"] = "/tmp/jumpscale_installer"
            # config["LOGGER_REDIS"] = False
            # config["LOGGER_CONSOLE"] = True

        if not "DIR_TEMP" in config:
            config["DIR_TEMP"] = "/tmp/jumpscale"
        if not "DIR_VAR" in config:
            config["DIR_VAR"] = "%s/var" % config["DIR_BASE"]
        if not "DIR_CODE" in config:
            config["DIR_CODE"] = self._codedir_get()
            # if Tools.exists("%s/code" % config["DIR_BASE"]):
            #     config["DIR_CODE"] = "%s/code" % config["DIR_BASE"]
            # else:
            #     config["DIR_CODE"] = "%s/code" % config["DIR_HOME"]
        if not "DIR_BIN" in config:
            config["DIR_BIN"] = "%s/bin" % config["DIR_BASE"]
        if not "DIR_APPS" in config:
            config["DIR_APPS"] = "%s/apps" % config["DIR_BASE"]

        if not "EXPLORER_ADDR" in config:
            config["EXPLORER_ADDR"] = "explorer.testnet.grid.tf"
        if not "THREEBOT_DOMAIN" in config:
            config["THREEBOT_DOMAIN"] = "3bot.testnet.grid.tf"

        if not "THREEBOT_CONNECT" in config:
            config["THREEBOT_CONNECT"] = True

        # max log msgpacks files on the file system each file is 1k logs
        if not "MAX_MSGPACKS_LOGS_COUNT" in config:
            config["MAX_MSGPACKS_LOGS_COUNT"] = 50
        if not "SSH_KEY_DEFAULT" in config:
            config["SSH_KEY_DEFAULT"] = ""

        if not "SSH_AGENT" in config:
            config["SSH_AGENT"] = True

        if not "USEGIT" in config:
            config["USEGIT"] = True

        return config

    def configure(self, config=None, readonly=None, debug=None, secret=None):
        """

        the args of the command line will also be parsed, will check for

        --readonly                      default is false
        --debug                         default debug is False

        :return:
        """

        if secret:
            self.secret_set(secret)

        basedir = self._basedir_get()

        if config:
            self.config.update(config)

        if readonly:
            self.config["READONLY"] = readonly

        if debug:
            self.config["DEBUG"] = debug

        # installpath = os.path.dirname(inspect.getfile(os.path))
        # # MEI means we are pyexe BaseInstaller
        # if installpath.find("/_MEI") != -1 or installpath.endswith("dist/install"):
        #     pass  # dont need yet but keep here

        if DockerFactory.indocker():
            self.config["IN_DOCKER"] = True
        else:
            self.config["IN_DOCKER"] = False

        self.config_save()
        self.init()

    @property
    def adminsecret(self):
        return self.secret_get()

    def test(self):
        if not MyEnv.loghandlers != []:
            Tools.shell()

    def excepthook(self, exception_type, exception_obj, tb, die=True, stdout=True, level=50):
        """
        :param exception_type:
        :param exception_obj:
        :param tb:
        :param die:
        :param stdout:
        :param level:
        :return: logdict see github/threefoldtech/jumpscaleX_core/docs/Internals/logging_errorhandling/logdict.md
        """
        if isinstance(exception_obj, Tools.exceptions.RemoteException):
            print(Tools.text_replace("{RED}*****Remote Exception*****{RESET}"))
            logdict = exception_obj.data
            Tools.log2stdout(logdict)

            exception_obj.data = None
            exception_obj.exception = None
        try:
            logdict = Tools.log(tb=tb, level=level, exception=exception_obj, stdout=stdout)
        except Exception as e:
            Tools.pprint("{RED}ERROR IN LOG HANDLER")
            print(e)
            ttype, msg, tb = sys.exc_info()
            traceback.print_exception(etype=ttype, tb=tb, value=msg)
            Tools.pprint("{RESET}")
            raise e
            sys.exit(1)

        exception_obj._logdict = logdict

        if self.debug and tb and pudb:
            # exception_type, exception_obj, tb = sys.exc_info()
            pudb.post_mortem(tb)

        if die is False:
            return logdict
        else:
            sys.exit(1)

    def exception_handle(self, exception_obj, die=True, stdout=True, level=50, stack_go_up=0):
        """
        e is the error as raised by e.g. try/except statement
        :param exception_obj: the exception obj coming from the try/except
        :param die: die if error
        :param stdout: if True send the error log to stdout
        :param level: 50 is error critical
        :return: logdict see github/threefoldtech/jumpscaleX_core/docs/Internals/logging_errorhandling/logdict.md

        example


        try:
            something
        except Exception as e:
            logdict = j.core.myenv.exception_handle(e,die=False,stdout=True)


        """
        ttype, msg, tb = sys.exc_info()
        return self.excepthook(ttype, exception_obj, tb, die=die, stdout=stdout, level=level)

    # def identity_set(self,name="default",):

    def config_edit(self):
        """
        edits the configuration file which is in {DIR_BASE}/cfg/jumpscale_config.toml
        {DIR_BASE} normally is /sandbox
        """
        Tools.file_edit(self.config_file_path)

    def _config_load(self):
        """
        loads the configuration file which default is in {DIR_BASE}/cfg/jumpscale_config.toml
        {DIR_BASE} normally is /sandbox
        """
        config = Tools.config_load(self.config_file_path)
        self.config = self.config_default_get(config)

    def config_save(self):
        Tools.config_save(self.config_file_path, self.config)

    def _state_load(self):
        """
        only 1 level deep toml format only for int,string,bool
        no multiline
        """
        if Tools.exists(self.state_file_path):
            self.state = Tools.config_load(self.state_file_path, if_not_exist_create=False)
        elif not self.readonly:
            self.state = Tools.config_load(self.state_file_path, if_not_exist_create=True)
        else:
            self.state = {}

    def state_save(self):
        if self.readonly:
            return
        Tools.config_save(self.state_file_path, self.state)

    def _key_get(self, key):
        key = key.split("=", 1)[0]
        key = key.split(">", 1)[0]
        key = key.split("<", 1)[0]
        key = key.split(" ", 1)[0]
        key = key.upper()
        return key

    def state_get(self, key):
        key = self._key_get(key)
        if key in self.state:
            return True
        return False

    def state_set(self, key):
        if self.readonly:
            return
        key = self._key_get(key)
        self.state[key] = True
        self.state_save()

    def state_delete(self, key):
        if self.readonly:
            return
        key = self._key_get(key)
        if key in self.state:
            self.state.pop(key)
            self.state_save()

    def states_delete(self, prefix):
        if self.readonly:
            return
        prefix = prefix.upper()
        keys = [i for i in self.state.keys()]
        for key in keys:
            if key.startswith(prefix):
                self.state.pop(key)
                # print("#####STATEPOP:%s" % key)
                self.state_save()

    def state_reset(self):
        """
        remove all state
        """
        Tools.delete(self.state_file_path)
        self._state_load()


MyEnv = MyEnv_()


class BaseInstaller:
    @staticmethod
    def install(force=False, sandboxed=False, branch=None, pips_level=3):

        MyEnv.init()

        if force:
            MyEnv.state_delete("install")

        if MyEnv.state_get("install"):
            return  # nothing to do

        BaseInstaller.base()
        if MyEnv.platform() == "linux":
            if not sandboxed:
                UbuntuInstaller.do_all()
            else:
                raise Tools.exceptions.Base("not ok yet")
                UbuntuInstaller.base(pips_level=pips_level)
        elif "darwin" in MyEnv.platform():
            if not sandboxed:
                OSXInstaller.do_all(pips_level=pips_level)
            else:
                raise Tools.exceptions.Base("not ok yet")
                OSXInstaller.base()
        else:
            raise Tools.exceptions.Base("only OSX and Linux Ubuntu supported.")

        for profile_name in [".bash_profile", ".profile"]:
            # BASHPROFILE
            if sandboxed:
                env_path = "%s/%s" % (MyEnv.config["DIR_HOME"], profile_name)
                if Tools.exists(env_path):
                    bashprofile = Tools.file_text_read(env_path)
                    cmd = "source %s/env.sh" % MyEnv._basedir_get()
                    if bashprofile.find(cmd) != -1:
                        bashprofile = bashprofile.replace(cmd, "")
                        Tools.file_write(env_path, bashprofile)
            else:
                # if not sandboxed need to remove old python's from bin dir
                Tools.execute("rm -f {DIR_BASE}/bin/pyth*", die_if_args_left=True)
                env_path = "%s/%s" % (MyEnv.config["DIR_HOME"], profile_name)
                if not Tools.exists(env_path):
                    bashprofile = ""
                else:
                    bashprofile = Tools.file_text_read(env_path)
                cmd = "source %s/env.sh" % MyEnv._basedir_get()
                if bashprofile.find(cmd) == -1:
                    bashprofile += "\n%s\n" % cmd
                    Tools.file_write(env_path, bashprofile)

        ji = JumpscaleInstaller()
        print("- get sandbox repos from git")
        ji.repos_get(pull=False, branch=branch)
        print("- copy files to sandbox (non binaries)")
        # will get the sandbox installed
        if not sandboxed:

            script = """
            set -e
            cd {DIR_BASE}
            rsync -rav {DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/sandbox/cfg/ {DIR_BASE}/cfg/
            rsync -rav {DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/sandbox/bin/ {DIR_BASE}/bin/
            #rsync -rav {DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/sandbox/openresty/ {DIR_BASE}/openresty/
            rsync -rav {DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/sandbox/env.sh {DIR_BASE}/env.sh
            mkdir -p root
            mkdir -p var

            """
            Tools.execute(script, interactive=MyEnv.interactive, die_if_args_left=True, replace=True)

        else:

            # install the sandbox

            raise Tools.exceptions.Base("not done yet")

            script = """
            cd {DIR_BASE}
            rsync -ra {DIR_BASE}/code/github/threefoldtech/sandbox_base/base/ {DIR_BASE}/
            mkdir -p root
            """
            Tools.execute(script, interactive=MyEnv.interactive, die_if_args_left=True)

            if MyEnv.platform() == "darwin":
                reponame = "sandbox_osx"
            elif MyEnv.platform() == "linux":
                reponame = "sandbox_ubuntu"
            else:
                raise Tools.exceptions.Base("cannot install, MyEnv.platform() now found")

            Tools.code_github_get(repo=reponame, branch=["master"])

            script = """
            set -e
            cd {DIR_BASE}
            rsync -ra code/github/threefoldtech/{REPONAME}/base/ .
            mkdir -p root
            mkdir -p var
            """
            args = {}
            args["REPONAME"] = reponame

            Tools.execute(script, interactive=MyEnv.interactive, args=args, die_if_args_left=True)

            script = """
            set -e
            cd {DIR_BASE}
            source env.sh
            python3 -c 'print("- PYTHON OK, SANDBOX USABLE")'
            """
            Tools.execute(script, interactive=MyEnv.interactive, die_if_args_left=True)

            Tools.log("INSTALL FOR BASE OK")

        MyEnv.state_set("install")

    @staticmethod
    def base():

        if MyEnv.state_get("generic_base"):
            return

        if not os.path.exists(MyEnv.config["DIR_TEMP"]):
            os.makedirs(MyEnv.config["DIR_TEMP"], exist_ok=True)

        script = """

        mkdir -p {DIR_TEMP}/scripts
        mkdir -p {DIR_VAR}/log

        """
        Tools.execute(script, interactive=True, die_if_args_left=True)

        if MyEnv.platform_is_osx:
            OSXInstaller.base()
        elif MyEnv.platform_is_linux:
            UbuntuInstaller.base()
        else:
            print("Only ubuntu & osx supported")
            os.exit(1)

        MyEnv.state_set("generic_base")

    @staticmethod
    def pips_list(level=3):
        """
        level0 is only the most basic
        1 in the middle (recommended)
        2 is all pips
        """

        # ipython==7.5.0 ptpython==2.0.4 prompt-toolkit==2.0.9

        pips = {
            # level 0: most basic needed
            0: [
                "cached_property",
                "captcha",
                "certifi",
                "click>=6.6",
                "pygments-github-lexers",
                "colored-traceback>=0.2.2",
                "colorlog>=2.10.0",
                # "credis",
                "psycopg2-binary",
                "numpy",
                "cryptocompare",
                "cryptography>=2.2.0",
                "dnslib",
                "ed25519>=1.4",
                "future>=0.15.0",
                "geopy",
                "geocoder",
                "gevent >= 1.2.2",
                "GitPython>=2.1.1",
                "grequests>=0.3.0",
                "httplib2>=0.9.2",
                "ipcalc>=1.99.0",
                "ipython>=7.5",
                "Jinja2>=2.9.6",
                "libtmux>=0.7.1",
                "msgpack-python>=0.4.8",
                "netaddr>=0.7.19",
                "netifaces>=0.10.6",
                "netstr",
                "npyscreen",
                "parallel_ssh>=1.4.0",
                "ssh2-python",
                "paramiko>=2.2.3",
                "path.py>=10.3.1",
                # "peewee", #DO NOT INSTALL PEEWEE !!!
                "psutil>=5.4.3",
                "pudb>=2017.1.2",
                "pyblake2>=0.9.3",
                "cython",
                "pycapnp>=0.5.12",
                "PyGithub>=1.34",
                "pymux>=0.13",
                "pynacl>=1.2.1",
                "pyOpenSSL>=17.0.0",
                "pyserial>=3.0",
                "python-dateutil>=2.5.3",
                "pytoml>=0.1.2",
                "pyyaml",
                "redis>=2.10.5",
                "requests>=2.13.0",
                "six>=1.10.0",
                "sendgrid",
                "toml>=0.9.2",
                "Unidecode>=0.04.19",
                "watchdog>=0.8.3",
                # "bpython",
                "pbkdf2",
                "ptpython==2.0.4",
                "prompt-toolkit==2.0.9",
                "pygments-markdown-lexer",
                "wsgidav",
                "bottle==0.12.17",  # why this version?
                "beaker",
                "Mnemonic",
                "xmltodict",
                "sonic-client",
                "watchdog_gevent",
                "python-digitalocean",
                "ujson",
                "stellar-sdk",
                "packet-python>=1.37",
                "gevent-websocket",
                "base58",
                "ansicolors",
                "better_exceptions",
            ],
            # level 1: in the middle
            1: [
                "Brotli>=0.6.0",
                "gipc",
                # "blosc>=1.5.1",  #don't think we use it, I hope
                "scikit-build",
                # "cmake",  #DO WE NEED THIS??? better not, takes for ever
                "zerotier>=1.1.2",
                "python-jose>=2.0.1",
                "itsdangerous>=0.24",
                "jsonschema>=2.5.1",
                "graphene>=2.0",
                "ovh>=0.4.7",
                # "uvloop>=0.8.0",  #think is not used
                "pycountry",
                "pycountry_convert",
                "cson>=0.7",
                "Pillow>=4.1.1",
                "bottle==0.12.17",
                "bottle-websocket==0.2.9",
            ],
            # level 2: full install
            2: [
                "pystache>=0.5.4",
                # "pypandoc>=1.3.3",
                # "SQLAlchemy>=1.1.9",
                "pymongo>=3.4.0",
                "docker>=3",
                "dnspython>=1.15.0",
                "etcd3>=0.7.0",
                "Flask-Inputs>=0.2.0",
                "Flask>=0.12.2",
                "html2text",
                "influxdb>=4.1.0",
                "google-api-python-client",
            ],
        }

        res = []

        for piplevel in pips:
            if piplevel <= level:
                res += pips[piplevel]

        return res

    @staticmethod
    def pips_install(items=None, pips_level=3):
        if not items:
            items = BaseInstaller.pips_list(pips_level)
            MyEnv.state_set("pip_zoos")
        assert isinstance(items, list)
        for pip in items:
            assert "," not in pip
            if not MyEnv.state_get("pip_%s" % pip):
                C = "pip3 install '%s'" % pip  # --user
                Tools.execute(C, die=True, retry=3)
                MyEnv.state_set("pip_%s" % pip)
        # C = "pip3 install -e 'git+https://github.com/threefoldtech/0-hub#egg=zerohub&subdirectory=client'"
        # Tools.execute(C, die=True)

    @staticmethod
    def code_copy_script_get():
        CMD = """
        cd /
        rm -rf /sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/threebot
        rm -rf  /sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot/alerta
        [ -d "/sandbox/code/github" ] && rsync -rav --exclude '__pycache__' --exclude '.git' --exclude '.idea' --exclude '*.pyc' /sandbox/code/github/threefoldtech/ /sandbox/code_org/

        """
        return Tools.text_strip(CMD, replace=False)

    @staticmethod
    def cleanup_script_get():
        CMD = """
        cd /
        rm -f /sandbox/cfg/.configured
        rm -f /tmp/cleanedup
        rm -f /root/.jsx_history
        rm -rf /root/.cache
        mkdir -p /root/.cache
        rm -rf /bd_build
        rm -rf /var/log
        mkdir -p /var/log
        rm -rf /var/mail
        mkdir -p /var/mail
        rm -rf /tmp
        mkdir -p /tmp
        chmod -R 0777 /tmp
        rm -rf /var/cache/luarocks
        apt remove nodejs -y
        apt-get clean -y
        apt-get autoremove --purge -y
        rm -rf /sandbox/openresty/pod
        rm -rf /sandbox/openresty/site
        rm -rf /sandbox/var
        mkdir -p /sandbox/var
        rm -f /sandbox/cfg/bcdb_config
        rm -f /sandbox/cfg/schema_meta.msgpack
        rm -rf /sandbox/cfg/bcdb
        rm -rf /sandbox/cfg/keys
        rm -rf /sandbox/cfg/nginx/default_openresty_threebot/static/weblibs
        rm -rf /sandbox/root
        rm -rf /usr/src
        #remove nodejs things
        find / | grep -E "(yarn|node_modules)" | xargs rm -rf 2>&1 > /dev/null
        rm -rf /usr/local/share/jupyter/lab/staging
        rm -f /sandbox/bin/openresty.old
        #remove apt cache
        rm -rf /var/lib/apt/lists
        mkdir -p /var/lib/apt/lists
        #non neccesary files
        find / | grep -E "(__pycache__|\.bak$|\.pyc$|\.pyo$|\.rustup|\.cargo)" | xargs rm -rf 2>&1 > /dev/null
        #IMPORTANT remove secret from config file
        if test -f "/sandbox/cfg/jumpscale_config.toml"; then
            sed -i -r 's/^SECRET =.*/SECRET =/' /sandbox/cfg/jumpscale_config.toml
        fi
        """
        return Tools.text_strip(CMD, replace=False)

    @staticmethod
    def cleanup_script_developmentenv_get():
        CMD = """
        apt remove gcc -y
        apt remove rustc -y
        apt remove llvm -y
        rm -rf  /sandbox/go
        rm -rf  /sandbox/go_proj
        apt-get remove --auto-remove golang-go -y
        rm -rf /usr/lib/x86_64-linux-gnu/libLLVM-6.0.so.1
        rm -rf /usr/lib/llvm-6.0
        rm -rf /usr/lib/llvm-9.0
        rm -rf /usr/lib/llvm-*.0
        rm -rf /usr/lib/llvm-*
        rm -rf /usr/lib/gcc
        find / | grep -E "(LLVM|llvm/)" | xargs rm -rf
        export SUDO_FORCE_REMOVE=no
        apt-mark manual wireguard-tools
        apt-mark manual sudo
        apt-get autoremove --purge -y
        rm -rf /var/lib/apt/lists
        mkdir -p /var/lib/apt/lists
        # rm -rf /sandbox/nodejs
        #remove libgcc
        rm -rf /usr/lib/gcc

        """
        return Tools.text_strip(CMD, replace=False)


class OSXInstaller:
    @staticmethod
    def do_all(pips_level=3):
        MyEnv.init()
        Tools.log("installing OSX version")
        OSXInstaller.base()
        BaseInstaller.pips_install(pips_level=pips_level)

    @staticmethod
    def base():
        MyEnv.init()
        OSXInstaller.brew_install()
        if not Tools.cmd_installed("curl") or not Tools.cmd_installed("unzip") or not Tools.cmd_installed("rsync"):
            script = """
            brew install curl unzip rsync tmux libssh2
            """
            # graphviz #TODO: need to be put elsewhere but not in baseinstaller
            Tools.execute(script, replace=True)
        BaseInstaller.pips_install(["click", "redis"])

    @staticmethod
    def brew_install():
        if not Tools.cmd_installed("brew"):
            cmd = 'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
            Tools.execute(cmd, interactive=True)

    @staticmethod
    def brew_uninstall():
        MyEnv.init()
        cmd = 'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/uninstall)"'
        Tools.execute(cmd, interactive=True)
        toremove = """
        sudo rm -rf /usr/local/.com.apple.installer.keep
        sudo rm -rf /usr/local/include/
        sudo rm -rf /usr/local/etc/
        sudo rm -rf /usr/local/var/
        sudo rm -rf /usr/local/FlashcardService/
        sudo rm -rf /usr/local/texlive/
        """
        Tools.execute(toremove, interactive=True)


class UbuntuInstaller:
    @staticmethod
    def do_all(prebuilt=False, pips_level=3):
        MyEnv.init()
        Tools.log("installing Ubuntu version")

        UbuntuInstaller.ensure_version()
        UbuntuInstaller.base()
        # UbuntuInstaller.ubuntu_base_install()
        if not prebuilt:
            UbuntuInstaller.python_dev_install()
        UbuntuInstaller.apts_install()
        if not prebuilt:
            BaseInstaller.pips_install(pips_level=pips_level)

    @staticmethod
    def ensure_version():
        MyEnv.init()
        if not os.path.exists("/etc/lsb-release"):
            raise Tools.exceptions.Base("Your operating system is not supported")

        return True

    @staticmethod
    def base():
        MyEnv.init()

        if MyEnv.state_get("base"):
            return

        rc, out, err = Tools.execute("lsb_release -a")
        if out.find("Ubuntu 18.04") != -1:
            bionic = True
        else:
            bionic = False

        if bionic:
            script = """
            if ! grep -Fq "deb http://mirror.unix-solutions.be/ubuntu/ bionic" /etc/apt/sources.list; then
                echo >> /etc/apt/sources.list
                echo "# Jumpscale Setup" >> /etc/apt/sources.list
                echo deb http://mirror.unix-solutions.be/ubuntu/ bionic main universe multiverse restricted >> /etc/apt/sources.list
            fi
            """
            Tools.execute(script, interactive=True, die=False)

        script = """
        apt-get update
        apt-get install -y mc wget python3 git tmux telnet
        set +e
        apt-get install python3-distutils -y
        set -e
        apt-get install python3-psutil -y
        apt-get install -y curl rsync unzip
        locale-gen --purge en_US.UTF-8
        apt-get install python3-pip -y
        apt-get install -y redis-server
        apt-get install locales -y

        """
        Tools.execute(script, interactive=True)

        if bionic and not DockerFactory.indocker():
            UbuntuInstaller.docker_install()

        MyEnv.state_set("base")

    @staticmethod
    def docker_install():
        if MyEnv.state_get("ubuntu_docker_install"):
            return
        script = """
        apt-get update
        apt-get upgrade -y --force-yes
        apt-get install sudo python3-pip  -y
        pip3 install pudb
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
        apt-get update
        sudo apt-get install docker-ce -y
        """
        Tools.execute(script, interactive=True)
        MyEnv.state_set("ubuntu_docker_install")

    @staticmethod
    def python_dev_install():
        if MyEnv.state_get("python_dev_install"):
            return

        Tools.log("installing jumpscale tools")

        script = """
        cd /tmp
        apt-get install -y build-essential
        #apt-get install -y python3.8-dev


        """
        rc, out, err = Tools.execute(script, interactive=True, timeout=300)
        if rc > 0:
            # lets try other time
            rc, out, err = Tools.execute(script, interactive=True, timeout=300)
        MyEnv.state_set("python_dev_install")

    @staticmethod
    def apts_list():
        return [
            "iproute2",
            "python-ufw",
            "ufw",
            "libpq-dev",
            "iputils-ping",
            "net-tools",
            "libgeoip-dev",
            "libcapnp-dev",
            "graphviz",
            "libssl-dev",
            "cmake",
            "fuse",
        ]

    @staticmethod
    def apts_install():
        for apt in UbuntuInstaller.apts_list():
            if not MyEnv.state_get("apt_%s" % apt):
                command = "apt-get install -y %s" % apt
                Tools.execute(command, die=True)
                MyEnv.state_set("apt_%s" % apt)


class JumpscaleInstaller:
    def install(
        self,
        sandboxed=False,
        force=False,
        gitpull=False,
        branch=None,
        threebot=False,
        identity=None,
        reset=None,
        jsinit=True,
        email=None,
        words=None,
        explorer=None,
        code_update_force=False,
    ):

        MyEnv.check_platform()
        # will check if there's already a key loaded (forwarded) will continue installation with it

        pips_level = 3

        BaseInstaller.install(sandboxed=sandboxed, force=force, branch=branch, pips_level=pips_level)

        Tools.file_touch(os.path.join(MyEnv.config["DIR_BASE"], "lib/jumpscale/__init__.py"))

        self.repos_get(pull=gitpull, branch=branch, reset=code_update_force)
        self.repos_link()
        self.cmds_link()
        # Install 3sdk to import installtools from it. as windows doesn't support symlinks
        Tools.execute("cd {DIR_CODE}/github/threefoldtech/jumpscaleX_core/install/; pip3 install -e . -q")
        if jsinit or not Tools.exists(os.path.join(MyEnv.config["DIR_BASE"], "lib/jumpscale/jumpscale_generated.py")):
            Tools.execute("cd {DIR_BASE};source env.sh;js_init generate", interactive=False, die_if_args_left=True)

        script = """
        set -e
        cd {DIR_BASE}
        source env.sh
        mkdir -p {DIR_BASE}/openresty/nginx/logs
        mkdir -p {DIR_BASE}/var/log
        # kosmos 'j.data.nacl.configure(generate=True,interactive=False)'
        # kosmos 'j.core.installer_jumpscale.remove_old_parts()'
        # kosmos --instruct=/tmp/instructions.toml
        # kosmos 'j.core.tools.pprint("JumpscaleX init step for encryption OK.")'
        """
        Tools.execute(script, die_if_args_left=True)

        # NOW JSX CAN BE USED (basic install done)

        if reset:
            Tools.execute("source /sandbox/env.sh;bcdb delete --all -f")

        if True or identity or threebot:

            if not identity:
                identity = ""
            if not email:
                email = ""
            if not words:
                words = ""
            if explorer:
                C = f"""
                j.clients.explorer.default_addr_set('{explorer}')
                j.me.configure(tname='{identity}',ask=False, email='{email}',words='{words}')
                """
                Tools.execute(C, die=True, interactive=True, jumpscale=True)

        if threebot:
            self.threebot_init(stop=True)

    def threebot_init(self, stop=False):
        print("START THREEBOT, can take upto 3-4 min for the first time")
        # build all dependencies
        Tools.execute_jumpscale("j.servers.threebot.install()")
        # now start to see we have all
        Tools.execute_jumpscale("j.servers.threebot.start(background=True)")
        timestop = time.time() + 240.0
        ok = False
        while not ok and time.time() < timestop:
            try:
                Tools.execute_jumpscale("assert j.core.db.get('threebot.started') == b'1'")
                ok = True
                break
            except:
                print(" - threebot starting")
                time.sleep(1)
        if not ok:
            raise Tools.exceptions.Base("could not stop threebot after install")
        print(" - Threebot Started")
        if stop:
            Tools.execute("j.servers.threebot.default.stop()", die=False, jumpscale=True, showout=False)
            time.sleep(2)
            Tools.execute("j.servers.threebot.default.stop()", die=True, jumpscale=True)
            print(" - Threebot stopped")

    def remove_old_parts(self):
        tofind = ["DigitalMe", "Jumpscale", "ZeroRobot"]
        for part in sys.path:
            if Tools.exists(part) and os.path.isdir(part):
                # print(" - REMOVE OLD PARTS:%s" % part)
                for item in os.listdir(part):
                    for item_tofind in tofind:
                        toremove = os.path.join(part, item)
                        if (
                            item.find(item_tofind) != -1
                            and toremove.find("sandbox") == -1
                            and toremove.find("github") == -1
                        ):
                            Tools.log("found old jumpscale item to remove:%s" % toremove)
                            Tools.delete(toremove)
                        if item.find(".pth") != -1:
                            out = ""
                            for line in Tools.file_text_read(toremove).split("\n"):
                                if line.find("threefoldtech") == -1:
                                    out += "%s\n" % line
                            try:
                                Tools.file_write(toremove, out)
                            except Exception:
                                pass
                            # Tools.shell()
        tofind = ["js_", "js9"]
        for part in os.environ["PATH"].split(":"):
            if Tools.exists(part):
                for item in os.listdir(part):
                    for item_tofind in tofind:
                        toremove = os.path.join(part, item)
                        if (
                            item.startswith(item_tofind)
                            and toremove.find("sandbox") == -1
                            and toremove.find("github") == -1
                        ):
                            Tools.log("found old jumpscale item to remove:%s" % toremove)
                            Tools.delete(toremove)

    # def prebuilt_copy(self):
    #     """
    #     copy the prebuilt files to the {DIR_BASE} location
    #     :return:
    #     """
    #     self.cmds_link(generate_js=False)
    #     # why don't we use our primitives here?
    #     Tools.execute("cp -a {DIR_CODE}/github/threefoldtech/sandbox_threebot_linux64/* /")
    #     # -a won't copy hidden files
    #     Tools.execute("cp {DIR_CODE}/github/threefoldtech/sandbox_threebot_linux64/.startup.toml /")
    #     Tools.execute("source {DIR_BASE}/env.sh; kosmos 'j.data.nacl.configure(generate=True,interactive=False)'")
    #

    def repos_get(self, pull=False, prebuilt=False, branch=None, reset=False, executor=None, shallow=False):
        assert not prebuilt  # not supported yet
        if prebuilt:
            GITREPOS["prebuilt"] = PREBUILT_REPO

        usessh = False if executor else Tools.code_github_use_ssh()
        execute = executor.execute if executor else Tools.execute

        repos = []
        foundurls = set()
        for NAME, repoinfo in GITREPOS.items():
            GITURL, BRANCH, RPATH, DEST = repoinfo
            if GITURL not in foundurls:
                repos.append({"name": NAME, "url": GITURL, "branch": BRANCH})
                foundurls.add(GITURL)

        count = len(repos)
        for idx, repo in enumerate(repos):
            print(f"Updating repo {repo['name']:<20} {idx+1}/{count}", end="\r")
            if usessh:
                repo["url"] = Tools.code_git_rewrite_url(repo["url"], ssh=True).url

            if branch:
                # check if provided branch exists otherwise don't use it
                C = f"""git ls-remote --heads {repo['url']} {branch} {repo['url']}"""
                _, out, _ = execute(C, showout=False, interactive=False)
                if out:
                    repo["branch"] = branch

            try:
                Tools.code_github_get(url=repo["url"], branch=repo["branch"], pull=pull, reset=reset, executor=executor, shallow=shallow)
            except Tools.exceptions.Input:
                raise

        print("")
        if prebuilt:
            self.prebuilt_copy()

    def repos_link(self):
        """
        link the jumpscale repo's to right location in sandbox
        :return:
        """

        for NAME, d in GITREPOS.items():
            GITURL, BRANCH, PATH, DEST = d

            (host, type, account, repo, url2, branch2, GITPATH, RPATH, port) = Tools.code_giturl_parse(url=GITURL)
            srcpath = "%s/%s" % (GITPATH, PATH)
            if not Tools.exists(srcpath):
                raise Tools.exceptions.Base("did not find:%s" % srcpath)

            DESTPARENT = os.path.dirname(DEST.rstrip())

            script = f"""
            set -e
            rm -f {DEST}
            mkdir -p {DESTPARENT}
            ln -s {GITPATH}/{PATH} {DEST}
            """
            Tools.execute(script, die_if_args_left=True)

    def cmds_link(self):
        _, _, _, _, loc = Tools._code_location_get(repo="jumpscaleX_core/", account="threefoldtech")
        for src in os.listdir("%s/cmds" % loc):
            src2 = os.path.join(loc, "cmds", src)
            dest = "%s/bin/%s" % (MyEnv.config["DIR_BASE"], src)
            if not os.path.exists(dest):
                Tools.link(src2, dest, chmod=770)
        Tools.link("%s/install/jsx.py" % loc, "{DIR_BASE}/bin/jsx", chmod=770)


class DockerFactory:

    _init = False
    _dockers = {}

    @staticmethod
    def indocker():
        """
        will check if we are in a docker
        :return:
        """
        rc, out, _ = Tools.execute("cat /proc/1/cgroup", die=False, showout=False)
        if rc == 0 and out.find("/docker/") != -1:
            return True
        return False

    @staticmethod
    def docker_assert():
        """
        will check if docker is installed and running
        :return:
        True if docker installed
        False if linux and docker not installed and it will be installed during installation process
        RuntimeError: windows or mac and docker is not installed and you must install it via gui
        """
        if MyEnv.platform_is_windows:
            _, out, _ = Tools.execute("docker -v", die=False)
            if "Docker" not in out:
                raise Tools.exceptions.RuntimeError(
                    "Docker is not installed or running please check: https://docs.docker.com/docker-for-windows/install/"
                )

        if MyEnv.platform_is_linux and not Tools.cmd_installed("docker"):
            return False

        if MyEnv.platform_is_osx and not Tools.cmd_installed("docker"):
            raise Tools.exceptions.RuntimeError(
                "Docker is not installed or running please check: https://docs.docker.com/"
            )

        return True

    @staticmethod
    def init(name=None):
        if not DockerFactory._init:
            if not MyEnv.platform_is_windows:
                rc, out, _ = Tools.execute("cat /proc/1/cgroup", die=False, showout=False)
                if rc == 0 and out.find("/docker/") != -1:
                    # nothing to do we are in docker already
                    return

                MyEnv.init()

                if not DockerFactory.docker_assert():
                    UbuntuInstaller.docker_install()
                    MyEnv._cmd_installed["docker"] = shutil.which("docker")

                # check if docker failed or on mac, can be installed with gui then
                if not DockerFactory.docker_assert():
                    raise Tools.exceptions.Operations("Could not find Docker installed")

                DockerFactory._init = True
                cdir = Tools.text_replace("{DIR_BASE}/var/containers")
                Tools.dir_ensure(cdir)
                for name_found in os.listdir(cdir):
                    if not os.path.isdir(os.path.join(cdir, name_found)):
                        # https://github.com/threefoldtech/jumpscaleX_core/issues/297
                        # in case .DS_Store is created when opened in finder
                        continue
                    # to make sure there is no recursive behaviour if called from a docker container
                    if name_found != name and name_found.strip().lower() not in ["shared"]:
                        DockerContainer(name_found)
            else:
                # Check for windows docker installed, only installed by gui
                DockerFactory.docker_assert()
                MyEnv.init()
                DockerFactory._init = True

    @staticmethod
    def container_delete(name):
        DockerFactory.init()
        assert name
        assert len(name) > 3
        if name in DockerFactory._dockers:
            docker = DockerFactory._dockers[name]
            docker.delete()
            if name in DockerFactory._dockers:
                DockerFactory._dockers.pop(name)

    @staticmethod
    def container_get(name, image="threefoldtech/3bot2", start=False, delete=False, ports=None, mount=True, pull=False):
        DockerFactory.init()
        assert name
        assert len(name) > 3
        if delete and name in DockerFactory._dockers:
            docker = DockerFactory._dockers[name]
            docker.delete()
            # needed because docker object is being retained
            docker.config.save()
            if name in DockerFactory._dockers:
                DockerFactory._dockers.pop(name)

        docker = None
        if name in DockerFactory._dockers:
            docker = DockerFactory._dockers[name]
            if docker.container_running:
                if mount:
                    if docker.info["Mounts"] == []:
                        # means the current docker has not been mounted
                        docker.stop()
                        docker.start(mount=True)
                else:
                    for mount in docker.info["Mounts"]:
                        if mount["Destination"] not in ["/sandbox/myhost", "/sandbox/code"]:
                            docker.stop()
                            docker.start(mount=False)
                            break
                return docker
        if not docker:
            docker = DockerContainer(name=name, image=image, ports=ports)
        if start:
            docker.start(mount=mount, pull=pull)
        return docker

    @staticmethod
    def containers_running():
        # IMPORTANT use single quotes in the outer and double in between
        # Windows needs " not '
        names = Tools.execute('docker ps --format="{{json .Names}}"', showout=False, replace=False)[1].split("\n")
        names = [i.strip("\"'") for i in names if i.strip() != ""]
        return names

    @staticmethod
    def containers_names():
        # IMPORTANT use single quotes in the outer and double in between
        # Windows needs " not '
        names = Tools.execute('docker container ls -a --format="{{json .Names}}"', showout=False, replace=False)[
            1
        ].split("\n")
        names = [i.strip("\"'") for i in names if i.strip() != ""]
        return names

    @staticmethod
    def containers():
        DockerFactory.init()
        return DockerFactory._dockers.values()

    @staticmethod
    def list():
        res = []
        for d in DockerFactory.containers():
            print(" - %-10s : %-15s : %-25s (sshport:%s)" % (d.name, d.config.ipaddr, d.config.image, d.config.sshport))
            res.append(d.name)
        return res

    @staticmethod
    def container_name_exists(name):
        return name in DockerFactory.containers_names()

    @staticmethod
    def image_names():
        # IMPORTANT use single quotes in the outer and double in between
        # Windows needs " not '
        names = Tools.execute('docker images --format="{{.Repository}}:{{.Tag}}"', showout=False, replace=False)[
            1
        ].split("\n")
        res = []
        for name in names:
            name = name.strip()
            name = name.strip("\"'")
            name = name.strip("\"'")
            if name == "":
                continue
            if ":" in name:
                name = name.split(":", 1)[0]
            res.append(name)

        return res

    @staticmethod
    def image_name_exists(name):
        if ":" in name:
            name = name.split(":")[0]
        return name in DockerFactory.image_names()

    @staticmethod
    def image_remove(name):
        if name in DockerFactory.image_names():
            Tools.log("remove container:%s" % name)
            Tools.execute("docker rmi -f %s" % name)

    @staticmethod
    def reset(images=True):
        """
        jsx containers-reset

        will stop/remove all containers
        if images==True will also stop/remove all images
        :return:
        """
        for name in DockerFactory.containers_names():
            d = DockerFactory.container_get(name)
            d.delete()

        # will get all images based on id
        # IMPORTANT use single quotes in the outer and double in between
        # Windows needs " not '
        names = Tools.execute('docker images --format="{{.ID}}"', showout=False, replace=False)[1].split("\n")
        for image_id in names:
            if image_id:
                Tools.execute("""docker rmi -f %s""" % image_id)

        Tools.delete(Tools.text_replace("{DIR_BASE}/var/containers"))

    # @staticmethod
    # def get_container_port_binding(container_name="3obt", port="9001/udp"):
    #     ports_bindings = Tools.execute(
    #         "docker inspect {container_name} --format={data}".format(
    #             container_name=container_name, data="'{{json .HostConfig.PortBindings}}'"
    #         ),
    #         showout=False,
    #         replace=False,
    #     )
    #     # Get and serialize the binding ports data
    #     all_ports_data = json.loads(ports_bindings[1])
    #     port_binding_data = all_ports_data.get(port, None)
    #     if not port_binding_data:
    #         raise Tools.exceptions.Input(
    #             f"Error happened during parsing the binding ports data from container {conitainer_name} and port {port}"
    #         )
    #
    #     host_port = port_binding_data[-1].get("HostPort")
    #     return host_port

    # @staticmethod
    # def container_running_with_udp_ports_wireguard():
    #     containers_ports = dict()
    #     containers_names = DockerFactory.containers_names()
    #     for name in containers_names:
    #         port_binding = DockerFactory.get_container_port_binding(container_name=name, port="9001/udp")
    #         containers_ports[name] = port_binding
    #     return containers_ports

    @staticmethod
    def get_container_ip_address(container_name="3bot"):
        container_ip = Tools.execute(
            "docker inspect {container_name} --format={data}".format(
                container_name=container_name, data="'{{json .NetworkSettings.Networks.bridge.IPAddress}}'"
            ),
            showout=False,
            replace=False,
        )[1].split("\n")
        if not container_ip:
            raise Tools.exceptions.Input(
                f"Error happened during parsing the container {container_name} ip address data "
            )
        # Get the data in the required format
        formatted_container_ip = container_ip[0].strip("\"'")
        return formatted_container_ip

    @staticmethod
    def containers_running_ip_address():
        containers_ip_addresses = dict()
        containers_names = DockerFactory.containers_names()
        for name in containers_names:
            container_ip = DockerFactory.get_container_ip_address(container_name=name)
            containers_ip_addresses[name] = container_ip
        return containers_ip_addresses


class DockerConfig:
    def __init__(self, name, image=None, startupcmd=None, delete=False, ports=None):
        """
        port config is as follows:

        start_range = 9000+portrange*10
        ssh = start_range
        wireguard = start_range + 1

        :param name:
        :param portrange:
        :param image:
        :param startupcmd:
        """
        self.name = name
        self.ports = ports

        self.path_vardir = Tools.text_replace("{DIR_BASE}/var/containers/{NAME}", args={"NAME": name})
        Tools.dir_ensure(self.path_vardir)
        Tools.dir_ensure(Tools.text_replace("{DIR_BASE}/myhost"))
        Tools.dir_ensure(Tools.text_replace("{DIR_BASE}/code"))
        self.path_config = "%s/docker_config.toml" % (self.path_vardir)
        # self.wireguard_pubkey

        if delete:
            Tools.delete(self.path_vardir)
            Tools.delete(self.path_config)

        if not Tools.exists(self.path_config):

            self.portrange = None

            if image:
                self.image = image
            else:
                self.image = "threefoldtech/3bot2"

            if startupcmd:
                self.startupcmd = startupcmd
            else:
                self.startupcmd = "/sbin/my_init"

        else:
            self.load()

        self.ipaddr = "localhost"  # for now no ipaddr in wireguard

    def _find_port_range(self):
        existingports = []
        for container in DockerFactory.containers():
            if container.name == self.name:
                continue
            if not container.config.portrange in existingports:
                existingports.append(container.config.portrange)

        for i in range(50):
            if i in existingports:
                continue
            port_to_check = 9000 + i * 10
            if not Tools.tcp_port_connection_test(ipaddr="localhost", port=port_to_check):
                self.portrange = i
                print(" - SSH PORT ON: %s" % port_to_check)
                return
        if not self.portrange:
            raise Tools.exceptions.Input("cannot find tcp port range for docker")
        self.sshport = 9000 + int(self.portrange) * 10

    def reset(self):
        """
        erase the past config
        :return:
        """
        Tools.delete(self.path_vardir)

    def done_get(self, name):
        name2 = "done_%s" % name
        if name2 not in self.__dict__:
            self.__dict__[name2] = False
            self.save()
        return self.__dict__[name2]

    def done_set(self, name):
        name2 = "done_%s" % name
        self.__dict__[name2] = True
        self.save()

    def done_reset(self, name=None):
        if not name:
            ks = [str(k) for k in self.__dict__.keys()]
            for name in ks:
                if name.startswith("done_"):
                    self.__dict__.pop(name)
        else:
            if name.startswith("done_"):
                name = name[5:]
            name2 = "done_%s" % name
            self.__dict__[name2] = False
            self.save()

    def val_get(self, name):
        if name not in self.__dict__:
            self.__dict__[name] = None
            self.save()
        return self.__dict__[name]

    def val_set(self, name, val=None):
        self.__dict__[name] = val
        self.save()

    def load(self):
        if not Tools.exists(self.path_config):
            raise Tools.exceptions.JSBUG("could not find config path for container:%s" % self.path_config)

        r = Tools.config_load(self.path_config, keys_lower=True)
        ports = r.pop("ports", None)
        if ports:
            self.ports = json.loads(ports)
        if r != {}:
            self.__dict__.update(r)

        assert isinstance(self.portrange, int)

        a = 9005 + int(self.portrange) * 10
        b = 9009 + int(self.portrange) * 10
        udp = 9001 + int(self.portrange) * 10
        ssh = 9000 + int(self.portrange) * 10
        http = 7000 + int(self.portrange) * 10
        https = 4000 + int(self.portrange) * 10
        httpnb = 5000 + int(self.portrange) * 10  # notebook
        self.sshport = ssh
        self.portrange_txt = "-p %s-%s:8005-8009" % (a, b)
        self.portrange_txt += " -p %s:80" % http
        self.portrange_txt += " -p %s:8888" % httpnb
        self.portrange_txt += " -p %s:443" % https
        self.portrange_txt += " -p %s:9001/udp" % udp
        self.portrange_txt += " -p %s:22" % ssh

    @property
    def ports_txt(self):
        txt = ""
        if self.portrange_txt:
            txt = self.portrange_txt
        if self.ports:
            for key, value in self.ports.items():
                txt += f" -p {key}:{value}"
        return txt

    def save(self):
        data = self.__dict__.copy()
        data["ports"] = json.dumps(data["ports"])
        Tools.config_save(self.path_config, data)
        assert isinstance(self.portrange, int)
        self.load()

    def __str__(self):
        return str(self.__dict__)

    __repr__ = __str__


class DockerContainer:
    def __init__(self, name="default", image=None, startupcmd=None, ports=None, identity=None):
        """
        if you want to start from scratch use: "phusion/baseimage:master"

        if codedir not specified will use {DIR_BASE}/code
        """
        if name == "shared":
            raise Tools.exceptions.JSBUG("should never be the shared obj")
        if not DockerFactory._init:
            raise Tools.exceptions.JSBUG("make sure to call DockerFactory.init() bedore getting a container")
        DockerFactory._dockers[name] = self

        self.config = DockerConfig(name=name, image=image, startupcmd=startupcmd, ports=ports)

        if self.config.portrange is None:
            self.config._find_port_range()
            self.config.save()

        self._wireguard = None
        self._executor = None

    def done_get(self, name):
        name = name.strip().lower()
        path = "/root/state/%s" % name
        try:
            self.dexec("cat %s" % path)
        except Exception:
            return False
        return True

    def done_set(self, name):
        name = name.strip().lower()
        path = "/root/state/%s" % name
        self.dexec("touch %s" % path)

    def done_reset(self, name=None):
        if not name:
            self.dexec("rm -rf /root/state")
            self.dexec("mkdir -p /root/state")
        else:
            name = name.strip().lower()
            path = "/root/state/%s" % name
            self.dexec("rm -f %s" % path)

    @property
    def executor(self):
        if not self._executor:
            self._executor = ExecutorDocker(self)
        return self._executor

    @property
    def container_exists_config(self):
        """
        returns True if the container is defined on the filesystem with the config file
        :return:
        """
        if Tools.exists(self._path):
            return True

    @property
    def mount_code_exists(self):
        m = self.info["Mounts"]
        for item in m:
            if item["Destination"] == "/sandbox/code":
                return True
        return False

    @property
    def container_exists_in_docker(self):
        return self.name in DockerFactory.containers_names()

    @property
    def container_running(self):
        return self.name in DockerFactory.containers_running()

    @property
    def _path(self):
        return self.config.path_vardir

    @property
    def image(self):
        return self.config.image

    @image.setter
    def image(self, val):
        val = self._image_clean(val)
        if self.config.image != val:
            self.config.image = val
            self.config.save()

    def _image_clean(self, image=None):
        if image is None:
            return self.config.image
        if ":" in image:
            image = image.split(":")[0]
        return image

    @property
    def name(self):
        return self.config.name

    def install(self, update=True, stop=False, delete=False):
        return self.start(update=update, stop=stop, delete=delete, mount=True)

    def start(self, stop=False, delete=False, update=False, ssh=None, mount=None, pull=False, image=None, portmap=True):
        """
        @param mount : will mount the code dir from the host or not, default True
            True means: will force the mount
            None means: don't check mounted or not
            False means: will make sure is not mounted
        @param stop: stop the container if it was started
        @param delete: delete the container if it was there
        @param update: update ubuntu and some required base modules
        @param ssh: make sure ssh has been configured so you can access if from local
            True means: use ssh & configure
            None means: don't impact sshconfig, just leave as it is right now, don't do anything
            False means: remove ssh config if there is one

        @param image: can overrule the specified image at config time, normally leave empty

        @param portmap: if you want to map ports from host to docker container

        """
        if not image:
            image = self.image
        if not self.container_exists_config:
            raise Tools.exceptions.Operations("ERROR: cannot find docker with name:%s, cannot start" % self.name)

        if pull:
            # lets make sure we have the latest image, ONLY DO WHEN FORCED, NOT STD
            Tools.execute(f"docker image pull {image}", interactive=True)
            stop = True  # means we need to stop now, because otherwise we can't know we start from right image

        if delete:
            self.delete()
        else:
            if stop:
                self.stop()

        if self.isrunning():
            if mount is True:
                if not self.mount_code_exists:
                    assert image is None  # because we are creating a new image, so cannot overrule
                    image = self._internal_image_save(stop=True)
            elif mount is False:
                if self.mount_code_exists:
                    assert image is None
                    image = self._internal_image_save(stop=True)

        if self.container_exists_in_docker:
            start_cmd = f"docker start {self.config.name}"
            Tools.execute(start_cmd, interactive=False)
            return

        if not image:
            image = self.config.image
        if ":" in image:
            image = image.split(":")[0]

        if self.isrunning():
            # means we did not start because of any mismatch, so we can return
            # if people want to make sure its new situation they need to force a stop
            if update or ssh:
                self._update(update=update, ssh=ssh)
            return

        # Now create the container
        DIR_CODE = MyEnv.config["DIR_CODE"] if not MyEnv.platform_is_windows else r"%s\code" % MyEnv._basedir_get()
        DIR_BASE = MyEnv.config["DIR_BASE"] if not MyEnv.platform_is_windows else MyEnv._basedir_get()
        DIR_IDENTITY = f"{DIR_BASE}/myhost" if not MyEnv.platform_is_windows else r"%s\myhost" % MyEnv._basedir_get()

        MOUNTS = ""
        if mount:
            MOUNTS = f"""
            -v {DIR_CODE}:/sandbox/code \
            -v {DIR_IDENTITY}:/sandbox/myhost
            """
            MOUNTS = Tools.text_strip(MOUNTS)
        else:
            MOUNTS = f"-v {DIR_IDENTITY}:/sandbox/myhost"

        if portmap:
            PORTRANGE = self.config.ports_txt
        else:
            PORTRANGE = ""

        if DockerFactory.image_name_exists(f"internal_{self.config.name}:") is not False:
            image = f"internal_{self.config.name}"

        run_cmd = f"docker run --name={self.config.name} --hostname={self.config.name} -d {PORTRANGE} \
        --device=/dev/net/tun --cap-add=NET_ADMIN --cap-add=SYS_ADMIN --cap-add=DAC_OVERRIDE \
        --cap-add=DAC_READ_SEARCH {MOUNTS} {image} {self.config.startupcmd}"

        run_cmd = Tools.text_strip(run_cmd)
        run_cmd2 = Tools.text_replace(re.sub(r"\s+", " ", run_cmd))
        print(" - Docker machine gets created: ")
        # print(run_cmd2)
        Tools.execute(run_cmd2, interactive=False)

        self._update(update=update, ssh=ssh)

        if not mount:
            # mount the code in the container to the right location to let jumpscale work
            assert self.mount_code_exists is False
            self.dexec("rm -rf /sandbox/code")
            self.dexec("mkdir -p /sandbox/code/github")
            self.dexec("ln -s /sandbox/code_org /sandbox/code/github/threefoldtech")

        self._log("start done")

    def _update(self, update=False, ssh=False):

        if True or ssh or update or not self.config.done_get("ssh"):
            print(" - Configure / Start SSH server")

            self.dexec("rm -rf /sandbox/cfg/keys", showout=False)
            self.dexec(
                "rm -f /root/.ssh/authorized_keys;/etc/init.d/ssh stop 2>&1 > /dev/null", die=False, showout=False
            )
            self.dexec("/usr/bin/ssh-keygen -A", showout=False)
            self.dexec("/etc/init.d/ssh start", showout=False)
            self.dexec("rm -f /etc/service/sshd/down", showout=False)

            SSHKEYS = Tools.execute("ssh-add -L", die=False, showout=False)[1]
            if SSHKEYS.strip() != "":
                if MyEnv.platform_is_windows:
                    SSHKEYS = SSHKEYS.strip("\r\n")
                    self.dexec("echo %s > /root/.ssh/authorized_keys" % SSHKEYS, showout=False)
                else:
                    self.dexec('echo "%s" > /root/.ssh/authorized_keys' % SSHKEYS, showout=False)

            if not MyEnv.platform_is_windows:
                Tools.execute(
                    "mkdir -p {0}/.ssh && touch {0}/.ssh/known_hosts".format(MyEnv.config["DIR_HOME"]), showout=False
                )

            # is to make sure we can login without interactivity
            Tools.known_hosts_update("localhost", self.config.sshport)

        # self.shell()

        self.dexec("mkdir -p /root/state")
        if update or not self.done_get("install_base"):
            print(" - Upgrade ubuntu")
            self.dexec("add-apt-repository ppa:wireguard/wireguard -y")
            self.dexec("apt-get update")
            self.dexec("DEBIAN_FRONTEND=noninteractive apt-get -y upgrade --force-yes")
            self.dexec("apt-get install mc git -y")
            self.dexec("apt-get install python3 python3-pip -y")
            self.dexec("pip3 install redis")
            self.dexec("apt-get install wget tmux -y")
            self.dexec("apt-get install curl rsync unzip redis-server htop -y")
            self.dexec("apt-get install python3-distutils python3-psutil python3-pip python3-click -y")
            self.dexec("locale-gen --purge en_US.UTF-8")
            self.dexec("apt-get install software-properties-common -y")
            self.dexec("apt-get install wireguard -y")
            self.dexec("apt-get install locales -y")
            self.done_set("install_base")
            print(" - Upgrade ubuntu ended")

        # cmd = "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' %s" % self.name
        # rc, out, err = Tools.execute(cmd, replace=False, showout=False, die=False)
        # if rc == 0:
        #     self.config.ipaddr = out.strip()
        #     self.config.save()

        # if DockerFactory.container_name_exists("3bot") and self.name != "3bot":
        #     d = DockerFactory.container_get("3bot")
        #     # print(" - Create route to main 3bot container")
        #     cmd = "ip route add 10.10.0.0/16 via %s" % d.config.ipaddr
        #     # TODO: why is this no longer done?

    @property
    def info(self):
        cmd = "docker inspect %s" % self.name
        rc, out, err = Tools.execute(cmd, replace=False, showout=False, die=False)
        if rc != 0:
            raise Tools.exceptions.Base("could not docker inspect:%s" % self.name)
        data = json.loads(out)[0]
        return data

    def dexec(self, cmd, interactive=False, die=True, showout=True, retry=None, errormsg=None):
        if "'" in cmd:
            cmd = cmd.replace("'", '"')

        # IMPORTANT use single quotes in the outer and double in between
        # Windows needs " not '
        if interactive:
            if MyEnv.platform_is_windows:
                cmd2 = 'docker exec -ti %s bash -c "%s"' % (self.name, cmd)
            else:
                cmd2 = "docker exec -ti %s bash -c '%s'" % (self.name, cmd)
        else:
            if MyEnv.platform_is_windows:
                cmd2 = 'docker exec -t %s bash -c "%s"' % (self.name, cmd)
            else:
                cmd2 = "docker exec -t %s bash -c '%s'" % (self.name, cmd)
        return Tools.execute(
            cmd2, interactive=interactive, showout=showout, replace=False, die=die, retry=retry, errormsg=errormsg
        )

    def shell(self, cmd=None):
        if not self.isrunning():
            self.start()
        if cmd:
            self.dexec("source /sandbox/env.sh;cd /sandbox;clear;%s" % cmd, interactive=True)
        else:
            self.dexec("source /sandbox/env.sh;cd /sandbox;clear;bash", interactive=True)

    def diskusage(self):
        """
        uses ncdu to visualize disk usage
        :return:
        """
        self.dexec("apt-get update;apt-get install ncdu -y;ncdu /", interactive=True)

    def execute(
        self,
        cmd,
        retry=None,
        showout=True,
        timeout=3600 * 2,
        die=True,
        jumpscale=False,
        python=False,
        replace=True,
        args=None,
        interactive=True,
    ):
        self.executor.execute(
            cmd,
            retry=retry,
            showout=showout,
            timeout=timeout,
            die=die,
            jumpscale=jumpscale,
            python=python,
            replace=replace,
            args=args,
            interactive=interactive,
        )

    def kosmos(self):
        self.execute(
            f"j.application.interactive={MyEnv.interactive}; j.shell(False)", interactive=True, jumpscale=True,
        )

    def stop(self):
        if self.container_running:
            Tools.execute("docker stop %s" % self.name, showout=False)

    def isrunning(self):
        if self.name in DockerFactory.containers_running():
            return True
        return False

    def restart(self):
        self.stop()
        self.start()

    def delete(self):
        """
        delete & remove the path with the config file to the container
        :return:
        """
        if self.container_exists_in_docker:
            self.stop()
            Tools.execute("docker rm -f %s" % self.name, die=False, showout=False)
        Tools.delete(self._path)
        if DockerFactory.image_name_exists(f"internal_{self.config.name}"):
            image = f"internal_{self.config.name}"
            Tools.execute("docker rmi -f %s" % image, die=True, showout=False)
        self.config.reset()
        if self.name in DockerFactory._dockers:
            DockerFactory._dockers.pop(self.name)

    @property
    def export_last_image_path(self):
        """
        readonly returns the last image created
        :return:
        """
        path = "%s/exports/%s.tar" % (self._path, self._export_image_last_version)
        return path

    @property
    def _export_image_last_version(self):
        dpath = "%s/exports/" % self._path
        highest = 0
        for item in os.listdir(dpath):
            try:
                version = int(item.replace(".tar", ""))
            except Exception:
                Tools.delete("%s/%s" % (dpath, item))
            if version > highest:
                highest = version
        return highest

    def import_(self, path=None, name=None, image=None, version=None):
        """

        :param path:  if not specified will be {DIR_BASE}/var/containers/$name/exports/$version.tar
        :param version: version of the export, if not specified & path not specified will be last in the path
        :param image: docker image name as used by docker to import to
        :param start: start the container after import
        :param mount: do you want to mount the dirs to host
        :param portmap: do you want to do the portmappings (ssh is always mapped)
        :return:
        """
        image = self._image_clean(image)

        if not path:
            if not name:
                if not version:
                    version = self._export_image_last_version
                path = "%s/exports/%s.tar" % (self._path, version)
            else:
                path = "%s/exports/%s.tar" % (self._path, name)
        if not Tools.exists(path):
            raise Tools.exceptions.Operations("could not find import file:%s" % path)

        if not path.endswith(".tar"):
            raise Tools.exceptions.Operations("export file needs to end with .tar")

        self.stop()
        DockerFactory.image_remove(image)

        print("import docker:%s to %s, will take a while" % (path, self.name))
        Tools.execute(f"docker import {path} {image}")
        self.config.image = image

    def export(self, path=None, name=None, version=None):
        """
        :param path:  if not specified will be {DIR_BASE}/var/containers/$name/exports/$version.tar
        :param version:
        :param overwrite: will remove the version if it exists
        :return:
        """
        dpath = "%s/exports/" % self._path
        if not Tools.exists(dpath):
            Tools.dir_ensure(dpath)

        if not path:
            if not name:
                if not version:
                    version = self._export_image_last_version + 1
                path = "%s/exports/%s.tar" % (self._path, version)
            else:
                path = "%s/exports/%s.tar" % (self._path, name)
        if Tools.exists(path):
            Tools.delete(path)
        print("export docker:%s to %s, will take a while" % (self.name, path))
        Tools.execute("docker export %s -o %s" % (self.name, path))
        return path

    def _internal_image_save(self, stop=False, image=None):
        if not image:
            image = f"internal_{self.name}"
        cmd = "docker rmi -f %s" % image
        Tools.execute(cmd, die=False, showout=False)
        cmd = "docker rmi -f %s:latest" % image
        Tools.execute(cmd, die=False, showout=False)
        cmd = "docker commit -p %s %s" % (self.name, image)
        Tools.execute(cmd)
        if stop:
            self.stop()
        return image

    def _log(self, msg):
        Tools.log(msg)

    def save(self, development=False, image=None, code_copy=False, clean=False):
        """

        :param clean: remove all files not needed for a runtime environment
        :param clean_devel: remove all files not needed for a development environment and a runtime environment
        :param image:
        :return:
        """
        image = self._image_clean(image)

        DockerFactory.image_remove("internal_%s" % self.config.name)

        def export_import(image, start=True):
            image2 = image.replace("/", "_")
            image2 = self._image_clean(image2)
            self.export(name=image2)
            self.import_(name=image2)
            self.start(mount=False)

        if code_copy:
            self._log("copy code")
            self.execute(BaseInstaller.code_copy_script_get())

        if clean:
            if self.mount_code_exists:
                self._log("save first, before start again without mounting")
                self._update()
                self._internal_image_save()
                self.stop()
                self.start(mount=False, update=False)
            # wait for docker to start and ssh become available
            time.sleep(10)
            self.execute(BaseInstaller.cleanup_script_get(), die=False)
            self.dexec("umount /sandbox/code", die=False)
            self.dexec("rm -rf /sandbox/code")

            if development:
                export_import("%s_dev" % image)
                self._internal_image_save(image="%s_dev" % image)

            self.execute(BaseInstaller.cleanup_script_developmentenv_get(), die=False)

            DockerFactory.image_remove("internal_%s" % self.config.name)
            DockerFactory.image_remove("internal_%s_dev" % self.config.name)

            export_import(image=image)

        else:
            self._update()
            self._internal_image_save()

        DockerFactory.image_remove("internal_%s" % self.config.name)

        self.config.save()

        # remove authorized keys
        self.dexec("rm -f /root/.ssh/*")
        self._internal_image_save(image=image)

        self.stop()
        self.delete()

    def push(self, image=None):
        if not image:
            image = self.image
        cmd = "docker push %s" % image
        Tools.execute(cmd)

    def _install_tcprouter(self):
        """
        Install tcprouter builder to be part of the image
        """
        self.execute(". /sandbox/env.sh; kosmos 'j.builders.network.tcprouter.install()'")

    def _install_package_dependencies(self):
        # self.execute("j.tools.threebot_packages._children.threefold__wikis.install()", jumpscale=True)
        Tools.shell()

    # def config_jumpscale(self):
    #     ##no longer ok, intent was to copy values from host but no longer the case
    #     CONFIG = {}
    #     for i in [
    #         "USEGIT",
    #         "DEBUG",
    #         "LOGGER_INCLUDE",
    #         "LOGGER_EXCLUDE",
    #         "LOGGER_LEVEL",
    #         # "LOGGER_CONSOLE",
    #         # "LOGGER_REDIS",
    #         "SECRET",
    #     ]:
    #         if i in MyEnv.config:
    #             CONFIG[i] = MyEnv.config[i]
    #     Tools.config_save(self._path + "/cfg/jumpscale_config.toml", CONFIG)
    #

    def install_jumpscale(
        self,
        secret=None,
        force=False,
        threebot=False,
        pull=False,
        redo=False,
        reset=False,
        identity=None,
        email=None,
        words=None,
        explorer=None,
    ):

        if not force:
            if not self.executor.state_exists("STATE_JUMPSCALE"):
                force = True

        if not force and threebot:
            if not self.executor.state_exists("STATE_THREEBOT"):
                force = True

        # if identity == "build":
        #     secret = "build"

        if not secret:
            secret = MyEnv.secret_get()

        args_txt = ""
        if redo:
            args_txt += " -r"
        if threebot:
            args_txt += " --threebot"
        if pull:
            args_txt += " --pull"
        if reset:
            args_txt += " --reset"
        if email:
            args_txt += f" --email={email}"
        if words:
            args_txt += f" --words='{words}'"
        if explorer:
            args_txt += f" --explorer='{explorer}'"

        if not MyEnv.interactive:
            args_txt += " --no-interactive"
        if identity:
            args_txt += f" -i {identity}"

        self.executor.execute(
            """
        rm -f /tmp/InstallTools.py
        rm -f /tmp/jsx
        ln -s /sandbox/code/github/threefoldtech/jumpscaleX_core/install/jsx.py /tmp/jsx
        """
        )

        # python3 jsx configure --sshkey {MyEnv.sshagent.key_default_name} -s
        # WHY DO WE NEED THIS, in container ssh-key should always be there & loaded, don't think there is a reason to configure it

        cmd = f"""
        cd /tmp
        #next will start redis and make sure secret is in there
        python3 jsx secret {secret}
        """
        print(" - Configure secret ")
        # best to set the secret first because otherwise we cannot be sure bcdb will work
        self.execute(cmd)

        cmd = f"""
        cd /tmp
        python3 jsx install {args_txt}
        """
        print(" - Installing jumpscaleX ")
        self.execute(cmd)
        print(" - Install succesfull")

        self.executor.state_set("STATE_JUMPSCALE")
        if threebot:
            self.executor.state_set("STATE_THREEBOT")

    def install_jupyter(self):
        self.execute(". /sandbox/env.sh; kosmos 'j.servers.notebook.install()'")

    def zerotier_connect(self):
        if not self.executor.state_exists("zerotier_installed"):
            self.execute("curl -s https://install.zerotier.com | sudo bash", die=False)
            self.executor.state_set("zerotier_installed")
        if not self.executor.state_exists("zerotier_joined"):
            self.execute("killall zerotier-one 2>&1 > /dev/null;zerotier-one -d")
            self.execute("zerotier-cli join 35c192ce9b01847c", die=False)
            self.executor.state_set("zerotier_joined")

        addr = None
        while not addr:
            print("waiting for zerotier to become live")
            rc, out, err = self.executor.execute("zerotier-cli listnetworks -j")
            Tools.clear()
            print("WAITING FOR ZEROTIER")
            print(out)
            r = json.loads(out)
            if len(r) == 1:
                r = r[0]
                if "assignedAddresses" in r:
                    addr = r["assignedAddresses"]
                    if len(addr) > 0:
                        addr = addr[0].split("/", 1)[0]
            else:
                self.execute("zerotier-cli join 35c192ce9b01847c", die=False)

        print(" - IP ADDRESS OF YOUR CONTAINER: %s" % addr)

        return addr

    def __repr__(self):
        return "# CONTAINER: \n %s" % Tools._data_serializer_safe(self.config.__dict__)

    __str__ = __repr__

    @property
    def wireguard(self):
        if not self._wireguard:
            self._wireguard = WireGuardServer(addr="127.0.0.1", port=self.config.sshport, myid=199)
        return self._wireguard


class SSHAgentKeyError(Exception):
    pass


class SSHAgent:
    def __init__(self):
        self._inited = False
        self._default_key = None
        self.autostart = True
        self.reset()

    @property
    def ssh_socket_path(self):

        if "SSH_AUTH_SOCK" in os.environ:
            return os.environ["SSH_AUTH_SOCK"]

        socketpath = Tools.text_replace("{DIR_VAR}/sshagent_socket")
        os.environ["SSH_AUTH_SOCK"] = socketpath
        return socketpath

    def _key_name_get(self, name=None):
        if not name:
            if MyEnv.config["SSH_KEY_DEFAULT"]:
                name = MyEnv.config["SSH_KEY_DEFAULT"]
            elif MyEnv.interactive:
                name = Tools.ask_string("give name for your sshkey,default='default'")
                if not name:
                    name = "default"
            else:
                name = "default"
        return name

    def key_generate(self, name=None, passphrase=None, reset=False):
        """
        Generate ssh key

        :param reset: if True, then delete old ssh key from dir, defaults to False
        :type reset: bool, optional
        """
        Tools.log("generate ssh key")
        if MyEnv.platform_is_windows:
            raise Tools.exceptions.RuntimeError(
                """Generating ssh-keys is not supported on windows due to ssh-agent problems.
        Please generate manually using `ssh-keygen -t ecdsa -b 521` then `ssh-add` and re-start the install"""
            )

        name = self._key_name_get(name)

        if not passphrase:
            if MyEnv.interactive:
                passphrase = Tools.ask_password("passphrase for ssh key to generate (empty=None)", emptyok=True)

        path = Tools.text_replace("{DIR_HOME}/.ssh/%s" % name)
        Tools.dir_ensure("{DIR_HOME}/.ssh")

        if reset:
            Tools.delete("%s" % path)
            Tools.delete("%s.pub" % path)

        if not Tools.exists(path) or reset:
            cmd = f'ssh-keygen -t rsa -f {path} -N "{passphrase}" -C {name}'
            Tools.execute(cmd, timeout=10)

            Tools.log("load generated sshkey: %s" % path)

        return path

    @property
    def key_default_name(self):
        """

        kosmos 'print(j.core.myenv.sshagent.key_default_name)'

        checks if it can find the default key for ssh-agent, if not will ask
        :return:
        """
        return self.init()

    def _ssh_keys_names_on_fs(self, hdir=None):
        DIR_HOME = MyEnv.config["DIR_HOME"]
        if not hdir:
            hdir = f"{DIR_HOME}/.ssh"
        choices = []
        if Tools.exists(hdir):
            for item in os.listdir(hdir):
                item2 = item.lower()
                if not (
                    item.startswith(".")
                    or item2.endswith((".pub", ".backup", ".toml", ".old"))
                    or item in ["known_hosts", "config", "authorized_keys"]
                ):
                    choices.append(item)
        return choices

    def init(self):
        DIR_HOME = MyEnv.config["DIR_HOME"]
        DIR_BASE = MyEnv.config["DIR_BASE"]

        def ask_key(key_names):
            if len(key_names) == 1:
                name = key_names[0]
            elif len(key_names) == 0:
                return None
            else:
                name = Tools.ask_choices("Which is your default sshkey to use", key_names)
            return name

        self._keys  # will fetch the keys if not possible will show error

        if "SSH_KEY_DEFAULT" in MyEnv.config and MyEnv.config["SSH_KEY_DEFAULT"]:
            sshkey = MyEnv.config["SSH_KEY_DEFAULT"]
            if sshkey not in self.key_names:
                res = self.key_load(name=sshkey, die=False)
                if res is None:
                    return None
                sshkey = None
                MyEnv.config["SSH_KEY_DEFAULT"] = ""
        else:
            sshkey = None

        # check if more than 1 key in ssh-agent
        if not sshkey:
            sshkey = ask_key(self.key_names)

        # no ssh key lets see if there are ssh keys in the default .ssh dir
        if not sshkey:
            choices = self._ssh_keys_names_on_fs()
            if len(choices) > 0:
                sshkey = ask_key(choices)

        myhost_sshkey_dir = f"{DIR_BASE}/myhost/sshkey"
        if not sshkey and Tools.exists(myhost_sshkey_dir):
            # lets check if there is a key in the myhost dir
            res = os.listdir(myhost_sshkey_dir)
            if len(res) == 1:
                sshkey = res[0]
                myhost_sshkey_path = f"{myhost_sshkey_dir}/{sshkey}"
                sshkeypath = f"{DIR_HOME}/.ssh/{sshkey}"
                shutil.copyfile(myhost_sshkey_path, sshkeypath)

        # if no key yet, need to generate
        if not sshkey:
            if Tools.ask_yes_no("ok to generate a default ssh key?"):
                sshkey = self._key_name_get()
                sshkeypath = self.key_generate(name=sshkey)
            else:
                print("CANNOT CONTINUE, PLEASE GENERATE AN SSHKEY AND RESTART")
                sys.exit(1)

        if sshkey not in self.key_names:
            if DockerFactory.indocker():
                raise Tools.exceptions.Base("sshkey should be passed forward by means of SSHAgent")
            self.key_load(name=sshkey)

        if sshkey not in self.key_names:
            raise Tools.exceptions.Input(f"SSH key '{sshkey}' was not loaded, should have been by now.")

        myhost_sshkey_path = f"{myhost_sshkey_dir}/{sshkey}"
        if not Tools.exists(myhost_sshkey_path):
            Tools.dir_ensure(myhost_sshkey_dir)
            sshkeypath = f"{DIR_HOME}/.ssh/{sshkey}"
            if Tools.exists(sshkeypath):
                shutil.copyfile(sshkeypath, myhost_sshkey_path)

        if MyEnv.config["SSH_KEY_DEFAULT"] != sshkey:
            MyEnv.config["SSH_KEY_DEFAULT"] = sshkey
            MyEnv.config_save()

        return sshkey

    def key_load(self, path=None, name=None, passphrase=None, duration=3600 * 24, die=True):
        """
        load the key on path

        :param path: path for ssh-key, can be left empty then we get the default name which will become path
        :param name: is the name of key which is in ~/.ssh/$name, can be left empty then will be default
        :param passphrase: passphrase for ssh-key, defaults to ""
        :type passphrase: str
        :param duration: duration, defaults to 3600*24
        :type duration: int, optional
        :raises RuntimeError: Path to load sshkey on couldn't be found
        :return: name,path
        """
        if not path and not name:
            raise Tools.exceptions.Input("name or path needs to be specified")
        if name:
            path = Tools.text_replace("{DIR_HOME}/.ssh/%s" % name)
        elif path:
            name = os.path.basename(path)

        if name in self.key_names:
            return

        if not Tools.exists(path):
            if not die:
                return 1
            raise Tools.exceptions.Base("Cannot find path:%s for sshkey (private key)" % path)

        Tools.log("load ssh key: %s" % path)
        os.chmod(path, 0o600)

        if passphrase:
            Tools.log("load with passphrase")
            C = """
                cd /tmp
                echo "exec cat" > ap-cat.sh
                chmod a+x ap-cat.sh
                export DISPLAY=1
                echo {passphrase} | SSH_ASKPASS=./ap-cat.sh ssh-add -t {duration} {path}
                """.format(
                path=path, passphrase=passphrase, duration=duration
            )
            rc, out, err = Tools.execute(C, showout=False, die=False)
            if rc > 0:
                Tools.delete("/tmp/ap-cat.sh")
                if not die:
                    return 2
                raise Tools.exceptions.Operations("Could not load sshkey with passphrase (%s)" % path)
        else:
            # load without passphrase
            cmd = "ssh-add -t %s %s " % (duration, path)
            rc, out, err = Tools.execute(cmd, showout=False, die=False)
            if rc > 0:
                if not die:
                    return 3
                raise Tools.exceptions.Operations("Could not load sshkey without passphrase (%s)" % path)

        self.keys_fix()

        self.reset()

        return name, path

    def keys_fix(self, hdir=None):
        """
        will make sure the pub keys are in the dir
        will also check security
        """
        DIR_HOME = MyEnv.config["DIR_HOME"]
        if not hdir:
            hdir = f"{DIR_HOME}/.ssh"
        for name in self._ssh_keys_names_on_fs(hdir):
            path_pub = f"{hdir}/{name}.pub"
            path_priv = f"{hdir}/{name}"
            if Tools.exists(path_priv) and not Tools.exists(path_pub):
                Tools.execute(f"ssh-keygen -y -f {path_priv} > {path_pub}")
            Tools.execute(f"chmod 644 {path_pub}")
            Tools.execute(f"chmod 600 {path_priv}")

    def key_unload(self, name):
        if name in self._keys:
            path = self.key_path_get(name)
            cmd = "ssh-add -d %s" % (path)
            rc, out, err = Tools.execute(cmd, showout=False, die=True)

    def keys_unload(self):
        cmd = "ssh-add -D"
        rc, out, err = Tools.execute(cmd, showout=False, die=True)

    @property
    def _keys(self):
        """
        """
        if self.__keys is None:
            self._read_keys()
        return self.__keys

    def _read_keys(self):
        return_code, out, err = Tools.execute("ssh-add -L", showout=False, die=False, timeout=2)
        if return_code:
            if return_code == 1 and out.find("The agent has no identities") != -1:
                self.__keys = []
                return []
            else:
                # Remove old socket if can't connect
                if Tools.exists(self.ssh_socket_path):
                    Tools.delete(self.ssh_socket_path)
                    # did not work first time, lets try again
                    return_code, out, err = Tools.execute("ssh-add -L", showout=False, die=False, timeout=10)

        if return_code and self.autostart:
            # ok still issue, lets try to start the ssh-agent if that could be done
            self.start()
            return_code, out, err = Tools.execute("ssh-add -L", showout=False, die=False, timeout=10)
            if return_code == 1 and out.find("The agent has no identities") != -1:
                self.__keys = []
                return []

        if return_code:
            return_code, out, err = Tools.execute("ssh-add", showout=False, die=False, timeout=10)
            if out.find("Error connecting to agent: No such file or directory"):
                raise SSHAgentKeyError("Error connecting to agent: No such file or directory")
            else:
                raise SSHAgentKeyError("Unknown error in ssh-agent, cannot find")

        keys = [line.split() for line in out.splitlines() if len(line.split()) == 3]
        self.__keys = list(map(lambda key: [key[2], " ".join(key[0:2])], keys))
        return self.__keys

    def reset(self):
        self.__keys = None

    @property
    def available(self):
        """
        Check if agent available (does not mean that the sshkey has been loaded, just checks the sshagent is there)
        :return: True if agent is available, False otherwise
        :rtype: bool
        """
        try:
            self._keys
        except SSHAgentKeyError:
            return False
        return True

    def keys_list(self, key_included=False):
        """
        kosmos 'print(j.clients.sshkey.keys_list())'
        list ssh keys from the agent

        :param key_included: defaults to False
        :type key_included: bool, optional
        :raises RuntimeError: Error during listing of keys
        :return: list of paths
        :rtype: list
        """
        if key_included:
            return self._keys
        else:
            return [i[0] for i in self._keys]

    @property
    def key_names(self):

        return [os.path.basename(i[0]) for i in self._keys]

    @property
    def key_paths(self):

        return [i[0] for i in self._keys]

    def key_path_get(self, keyname=None, die=True):
        """
        Returns Path of private key that is loaded in the agent

        :param keyname: name of key loaded to agent to get its path, if empty will check if there is 1 loaded, defaults to ""
        :type keyname: str, optional
        :param die:Raise error if True,else do nothing, defaults to True
        :type die: bool, optional
        :raises RuntimeError: Key not found with given keyname
        :return: path of private key
        :rtype: str
        """
        if not keyname:
            keyname = self.key_default_name
        else:
            keyname = os.path.basename(keyname)
        for item in self.keys_list():
            item2 = os.path.basename(item)
            if item2.lower() == keyname.lower():
                return item
        if die:
            raise Tools.exceptions.Base(
                "Did not find key with name:%s, check its loaded in ssh-agent with ssh-add -l" % keyname
            )

    # def keypub_path_get(self, keyname=None):
    #     path = self.key_path_get(keyname)
    #     return path + ".pub"

    @property
    def keypub(self):
        ks = MyEnv.sshagent._read_keys()
        if len(ks) > 0:
            return ks[0][1]

    def profile_js_configure(self):
        """
        kosmos 'j.clients.sshkey.profile_js_configure()'
        """

        bashprofile_path = os.path.expanduser("~/.profile")
        if not Tools.exists(bashprofile_path):
            Tools.execute("touch %s" % bashprofile_path)

        content = Tools.readFile(bashprofile_path)
        out = ""
        for line in content.split("\n"):
            if line.find("#JSSSHAGENT") != -1:
                continue
            if line.find("SSH_AUTH_SOCK") != -1:
                continue

            out += "%s\n" % line

        out += '[ -z "SSH_AUTH_SOCK" ] && export SSH_AUTH_SOCK=%s' % self.ssh_socket_path
        out = out.replace("\n\n\n", "\n\n")
        out = out.replace("\n\n\n", "\n\n")
        Tools.writeFile(bashprofile_path, out)

    def start(self):
        """

        start ssh-agent, kills other agents if more than one are found

        :raises RuntimeError: Couldn't start ssh-agent
        :raises RuntimeError: ssh-agent was not started while there was no error
        :raises RuntimeError: Could not find pid items in ssh-add -l
        """

        socketpath = self.ssh_socket_path

        Tools.process_kill_by_by_filter("ssh-agent", True)

        Tools.delete(socketpath)

        if not Tools.exists(socketpath):
            Tools.log("start ssh agent")
            Tools.dir_ensure("{DIR_VAR}")
            rc, out, err = Tools.execute("ssh-agent -a %s" % socketpath, die=False, showout=False, timeout=20)
            if rc > 0:
                raise Tools.exceptions.Base("Could not start ssh-agent, \nstdout:%s\nstderr:%s\n" % (out, err))
            else:
                if not Tools.exists(socketpath):
                    err_msg = "Serious bug, ssh-agent not started while there was no error, " "should never get here"
                    raise Tools.exceptions.Base(err_msg)

                # get pid from out of ssh-agent being started
                piditems = [item for item in out.split("\n") if item.find("pid") != -1]

                # print(piditems)
                if len(piditems) < 1:
                    Tools.log("results was: %s", out)
                    raise Tools.exceptions.Base("Cannot find items in ssh-add -l")

                # pid = int(piditems[-1].split(" ")[-1].strip("; "))
                # socket_path = j.sal.fs.joinPaths("/tmp", "ssh-agent-pid")
                # j.sal.fs.writeFile(socket_path, str(pid))

            return

        self.reset()

    def kill(self):
        """
        Kill all agents if more than one is found

        """
        Tools.process_kill_by_by_filter("ssh-agent", True)
        Tools.delete(self.ssh_socket_path)
        # Tools.delete("/tmp", "ssh-agent-pid"))
        self.reset()


class Executor:
    def __init__(self, addr=None, port=22, debug=False, name="executor"):
        self.name = name
        self.addr = addr
        self.port = port
        self.debug = debug
        self._id = None
        self._env = {}
        self._config = {}
        self.readonly = False
        self.CURDIR = ""
        self._data_path = "/var/executor_data"
        self._init()

    def reset(self):
        self.state_reset()
        self._init()
        self.save()

    def _init(self):
        self._config = None
        # self._env_on_system = None

    @property
    def config(self):
        if not self._config:
            self.load()
        return self._config

    def load(self):
        if self.exists(self._data_path):
            data = self.file_read(self._data_path, binary=True)
            self._config = pickle.loads(data)
        else:
            self._config = {}
        if "DIR_BASE" not in self._config:
            self.systemenv_load()
            self.save()

    def cmd_installed(self, cmd):
        rc, out, err = self.execute("which %s" % cmd, die=False, showout=False)
        if rc > 0:
            return False
        return True

    def save(self):
        """
        only relevant for ssh
        :return:
        """
        data = pickle.dumps(self.config)
        self.file_write(self._data_path, data)

    def delete(self, path):
        path = self._replace(path)
        cmd = "rm -rf %s" % path
        self.execute(cmd)

    def exists(self, path):
        path = self._replace(path)
        rc, _, _ = self.execute("test -e %s" % path, die=False, showout=False)
        if rc > 0:
            return False
        else:
            return True

    def _replace(self, content, args=None):
        """
        args will be substitued to .format(...) string function https://docs.python.org/3/library/string.html#formatspec
        MyEnv.config will also be given to the format function
        content example:
        "{name!s:>10} {val} {n:<10.2f}"  #floating point rounded to 2 decimals
        performance is +100k per sec
        """
        return Tools.text_replace(content=content, args=args, executor=self)

    def dir_ensure(self, path):
        cmd = "mkdir -p %s" % path
        self.execute(cmd, interactive=False)

    def path_isdir(self, path):
        """
        checks if the path is a directory
        :return:
        """
        rc, out, err = self.execute('if [ -d "%s" ] ;then echo DIR ;fi' % path, interactive=False)
        return out.strip() == "DIR"

    def path_isfile(self, path):
        """
        checks if the path is a directory
        :return:
        """
        rc, out, err = self.execute('if [ -f "%s" ] ;then echo FILE ;fi' % path, interactive=False)
        return out.strip() == "FILE"

    @property
    def platformtype(self):
        raise Tools.exceptions("not implemented")

    def file_read(self, path, binary=False):
        Tools.log("file read:%s" % path)
        if not binary:
            rc, out, err = self.execute("cat %s" % path, showout=False, interactive=False)
            return out
        else:
            p = Tools._file_path_tmp_get("data")
            self.download(path, dest=p)
            data = Tools.file_read(p)
            Tools.delete(p)
            return data

    def file_write(self, path, content, mode=None, owner=None, group=None, showout=True):
        """
        @param append if append then will add to file
        """
        path = self._replace(path)
        if showout:
            Tools.log("file write:%s" % path)

        assert isinstance(path, str)
        # if isinstance(content, str) and not "'" in content:
        #
        #     cmd = 'echo -n -e "%s" > %s' % (content, path)
        #     self.execute(cmd)
        # else:
        temp = Tools._file_path_tmp_get(ext="data")
        Tools.file_write(temp, content)
        self.upload(temp, path)
        Tools.delete(temp)
        cmd = ""
        if mode:
            cmd += "chmod %s %s && " % (mode, path)
        if owner:
            cmd += "chown %s %s && " % (owner, path)
        if group:
            cmd += "chgrp %s %s &&" % (group, path)
        cmd = cmd.strip().strip("&")
        if cmd:
            self.execute(cmd, showout=False, interactive=False)

        return None

    def find(self, path):
        rc, out, err = self.execute("find %s" % path, die=False, interactive=False)
        if rc > 0:
            if err.lower().find("no such file") != -1:
                return []
            raise Tools.exceptions.Base("could not find:%s \n%s" % (path, err))
        res = []
        for line in out.split("\n"):
            if line.strip() == path:
                continue
            if line.strip() == "":
                continue
            res.append(line)
        res.sort()
        return res

    @property
    def container_check(self):
        """
        means we don't work with ssh-agent ...
        """

        if "IN_DOCKER" not in self.config:
            rc, out, _ = self.execute("cat /proc/1/cgroup", die=False, showout=False, interactive=False)
            if rc == 0 and out.find("/docker/") != -1:
                self.config["IN_DOCKER"] = True
            else:
                self.config["IN_DOCKER"] = False
            self.save()
        return self.config["IN_DOCKER"]

    @property
    def state(self):
        if "state" not in self.config:
            self.config["state"] = {}
        return self.config["state"]

    def state_exists(self, key):
        key = Tools.text_strip_to_ascii_dense(key)
        return key in self.state

    def state_set(self, key, val=None, save=True):
        key = Tools.text_strip_to_ascii_dense(key)
        if save or key not in self.state or self.state[key] != val:
            self.state[key] = val
            self.save()

    def state_get(self, key, default_val=None):
        key = Tools.text_strip_to_ascii_dense(key)
        if key not in self.state:
            if default_val:
                self.state[key] = default_val
                return default_val
            else:
                return None
        else:
            return self.state[key]

    def state_delete(self, key):
        key = Tools.text_strip_to_ascii_dense(key)
        if key in self.state:
            self.state.pop(key)
            self.save()

    def systemenv_load(self):
        """
        get relevant information from remote system e.g. hostname, env variables, ...
        :return:
        """
        C = """
        set +ex
        if [ -e /sandbox ]; then
            export PBASE=/sandbox
        else
            export PBASE=~/sandbox
        fi
        ls $PBASE  > /dev/null 2>&1 && echo 'ISSANDBOX = 1' || echo 'ISSANDBOX = 0'
        ls "$PBASE/bin/python3"  > /dev/null 2>&1 && echo 'ISSANDBOX_BIN = 1' || echo 'ISSANDBOX_BIN = 0'
        echo UNAME = \""$(uname -mnprs)"\"
        echo "HOME = $HOME"
        echo HOSTNAME = "$(hostname)"
        if [[ "$(uname -s)" == "Darwin" ]]; then
            echo OS_TYPE = "darwin"
        else
            echo OS_TYPE = "ubuntu"
        fi
        echo "CFG_JUMPSCALE = --TEXT--"
        cat $PBASE/cfg/jumpscale_config.msgpack 2>/dev/null || echo ""
        echo --TEXT--
        echo "BASHPROFILE = --TEXT--"
        cat $HOME/.profile_js 2>/dev/null || echo ""
        echo --TEXT--
        echo "ENV = --TEXT--"
        export
        echo --TEXT--
        """
        print(" - load systemenv")

        rc, out, err = self.execute(C, showout=False, interactive=False, replace=False)
        res = {}
        state = ""
        for line in out.split("\n"):
            if line.find("--TEXT--") != -1 and line.find("=") != -1:
                varname = line.split("=")[0].strip().lower()
                state = "TEXT"
                txt = ""
                continue

            if state == "TEXT":
                if line.strip() == "--TEXT--":
                    res[varname.upper()] = txt
                    state = ""
                    continue
                else:
                    txt += line + "\n"
                    continue

            if "=" in line:
                varname, val = line.split("=", 1)
                varname = varname.strip().lower()
                val = str(val).strip().strip('"')
                if val.lower() in ["1", "true"]:
                    val = True
                elif val.lower() in ["0", "false"]:
                    val = False
                else:
                    try:
                        val = int(val)
                    except BaseException:
                        pass
                res[varname.upper()] = val

        if res["CFG_JUMPSCALE"].strip() != "":
            rconfig = Tools.config_load(content=res["CFG_JUMPSCALE"])
            res["CFG_JUMPSCALE"] = rconfig
        else:
            res["CFG_JUMPSCALE"] = {}

        envdict = {}
        for line in res["ENV"].split("\n"):
            line = line.replace("declare -x", "")
            line = line.strip()
            if line.strip() == "":
                continue
            if "=" in line:
                pname, pval = line.split("=", 1)
                pval = pval.strip("'").strip('"')
                envdict[pname.strip().upper()] = pval.strip()

        res["ENV"] = envdict

        def get_cfg(name, default):
            name = name.upper()
            if "CFG_JUMPSCALE" in res and name in res["CFG_JUMPSCALE"]:
                self._config[name] = res["CFG_JUMPSCALE"][name]
                return
            if name not in self._config:
                self._config[name] = default

        if self._config is None:
            self._config = {}

        get_cfg("DIR_HOME", res["ENV"]["HOME"])
        get_cfg("DIR_BASE", "/sandbox")
        get_cfg("DIR_CFG", "%s/cfg" % self.config["DIR_BASE"])
        get_cfg("DIR_TEMP", "/tmp")
        get_cfg("DIR_VAR", "%s/var" % self.config["DIR_BASE"])
        get_cfg("DIR_CODE", "%s/code" % self.config["DIR_BASE"])
        get_cfg("DIR_BIN", "/usr/local/bin")

    def execute(
        self,
        cmd,
        die=True,
        showout=False,
        timeout=1000,
        sudo=False,
        replace=True,
        interactive=False,
        retry=None,
        args=None,
        python=False,
        jumpscale=False,
        debug=False,
    ):
        original_command = cmd + ""
        if not args:
            args = {}

        tempfile, cmd = Tools._cmd_process(
            cmd=cmd,
            python=python,
            jumpscale=jumpscale,
            die=die,
            env=args,
            sudo=sudo,
            debug=debug,
            replace=replace,
            executor=self,
        )

        Tools._cmd_check(cmd)

        if interactive:
            if MyEnv.platform_is_windows:
                cmd2 = 'ssh -oStrictHostKeyChecking=no -t root@%s -A -p %s "%s"' % (self.addr, self.port, cmd)
            else:
                cmd2 = "ssh -oStrictHostKeyChecking=no -t root@%s -A -p %s '%s'" % (self.addr, self.port, cmd)
        else:
            if MyEnv.platform_is_windows:
                cmd2 = 'ssh -oStrictHostKeyChecking=no root@%s -A -p %s "%s"' % (self.addr, self.port, cmd)
            else:
                cmd2 = "ssh -oStrictHostKeyChecking=no root@%s -A -p %s '%s'" % (self.addr, self.port, cmd)

        r = Tools.execute(
            cmd2,
            interactive=interactive,
            showout=showout,
            timeout=timeout,
            retry=retry,
            die=die,
            original_command=original_command,
        )

        if tempfile:
            Tools.delete(tempfile)
        return r

    def upload(
        self,
        source,
        dest=None,
        recursive=True,
        createdir=False,
        rsyncdelete=True,
        ignoredir=None,
        ignorefiles=None,
        keepsymlinks=True,
        retry=4,
    ):
        """
        :param source:
        :param dest:
        :param recursive:
        :param createdir:
        :param rsyncdelete:
        :param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache__']
        :param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]
        :param keepsymlinks:
        :param showout:
        :return:
        """
        source = self._replace(source)
        if not dest:
            dest = source
        else:
            dest = self._replace(dest)
        if not os.path.exists(source):
            raise Tools.exceptions.Input("path '%s' not found" % source)

        if os.path.isfile(source):
            if createdir:
                destdir = os.path.dirname(source)
                self.dir_ensure(destdir)
            cmd = "scp -P %s %s root@%s:%s" % (self.port, source, self.addr, dest)
            if MyEnv.platform_is_windows:
                Tools.execute(cmd, showout=True, interactive=False)
            else:
                Tools._execute(cmd, showout=True, interactive=False)
            return
        raise Tools.exceptions.RuntimeError("not implemented")
        dest = self._replace(dest)
        if dest[0] != "/":
            raise Tools.exceptions.RuntimeError("need / in beginning of dest path")
        if source[-1] != "/":
            source += "/"
        if dest[-1] != "/":
            dest += "/"
        dest = "%s@%s:%s" % (self.login, self.addr, dest)

    def download(self, source, dest=None, ignoredir=None, ignorefiles=None, recursive=True):
        """
        :param source:
        :param dest:
        :param recursive:
        :param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache__']
        :param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]
        :return:
        """
        if not dest:
            dest = source
        else:
            dest = self._replace(dest)
        source = self._replace(source)

        sourcedir = os.path.dirname(source)
        Tools.dir_ensure(sourcedir)

        destdir = os.path.dirname(dest)
        Tools.dir_ensure(destdir)

        cmd = "scp -P %s root@%s:%s %s" % (self.port, self.addr, source, dest)
        if not MyEnv.platform_is_windows:
            Tools._execute(cmd, showout=True, interactive=False)
        else:
            Tools.execute(cmd, showout=True, interactive=False)

    def kosmos(self):
        self.jsxexec("j.shell()")

    @property
    def uid(self):
        if "uid" not in self.config:
            self.config["uid"] = str(random.getrandbits(32))
            self.save()
        return self.config["uid"]

    def state_reset(self):
        self.config["state"] = {}
        self.save()


class ExecutorSSH(Executor):
    def __init__(self, addr=None, port=22, debug=False, name="executor"):
        self.name = name
        self.addr = addr
        self.port = port
        self.debug = debug
        self._id = None
        self._env = {}
        self._config = {}
        self.readonly = False
        self.CURDIR = ""
        self._data_path = "/var/executor_data"
        self._init()


class ExecutorLocal(Executor):
    def execute(
        self,
        cmd,
        die=True,
        showout=False,
        timeout=1000,
        replace=True,
        interactive=False,
        retry=None,
        args=None,
        python=False,
        jumpscale=False,
        debug=False,
        errormsg=None,
    ):
        return Tools.execute(
            cmd,
            showout=showout,
            die=die,
            timeout=timeout,
            replace=replace,
            interactive=interactive,
            retry=retry,
            args=args,
            python=python,
            jumpscale=jumpscale,
            debug=debug,
            errormsg=errormsg,
        )

    def exists(self, path):
        return os.path.exists(path)

    def delete(self, path):
        path = self._replace(path)
        shutil.rmtree(path)

    def cmd_installed(self, cmd):
        return Tools.cmd_installed(cmd)


class ExecutorDocker(Executor):
    def __init__(self, container):
        self.name = "dockerexecutor"
        self._container = container
        self._id = None
        self._env = {}
        self._config = {}
        self.readonly = False
        self.CURDIR = ""
        self._data_path = "/var/executor_data"
        self._init()

    def execute(
        self,
        cmd,
        die=True,
        showout=False,
        timeout=1000,
        replace=True,
        interactive=False,
        retry=None,
        args=None,
        python=False,
        jumpscale=False,
        debug=False,
        errormsg=None,
    ):
        if not args:
            args = {}

        tempfile, cmd = Tools._cmd_process(
            cmd=cmd, python=python, jumpscale=jumpscale, die=die, env=args, debug=debug, replace=replace, executor=self,
        )

        Tools._cmd_check(cmd)
        r = self._container.dexec(
            cmd, interactive=interactive, die=die, retry=retry, errormsg=errormsg, showout=showout
        )
        if tempfile:
            Tools.delete(tempfile)
        return r

    def download(self, source, dest=None, ignoredir=None, ignorefiles=None, recursive=True):
        """
        :param source:
        :param dest:
        :param recursive:
        :param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache__']
        :param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]
        :return:
        """
        if not dest:
            dest = source
        else:
            dest = self._replace(dest)
        source = self._replace(source)

        sourcedir = os.path.dirname(source)
        Tools.dir_ensure(sourcedir)

        destdir = os.path.dirname(dest)
        Tools.dir_ensure(destdir)

        cmd = f"docker cp {self._container.name}:{source} {dest}"
        Tools.execute(cmd, showout=False, interactive=False)

    def upload(
        self,
        source,
        dest=None,
        recursive=True,
        createdir=False,
        rsyncdelete=True,
        ignoredir=None,
        ignorefiles=None,
        keepsymlinks=True,
        retry=4,
    ):
        """
        :param source:
        :param dest:
        :param recursive:
        :param createdir:
        :param rsyncdelete:
        :param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache__']
        :param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]
        :param keepsymlinks:
        :param showout:
        :return:
        """
        source = self._replace(source)
        if not dest:
            dest = source
        else:
            dest = self._replace(dest)
        if not os.path.exists(source):
            raise Tools.exceptions.Input("path '%s' not found" % source)

        if os.path.isfile(source):
            if createdir:
                destdir = os.path.dirname(source)
                self.dir_ensure(destdir)
            cmd = f"docker cp {source} {self._container.name}:{dest}"
            Tools.execute(cmd, showout=False, interactive=False)
            return
        raise Tools.exceptions.RuntimeError("not implemented")


class Registry:
    def __init__(self):
        self.addr = ["134.209.83.144"]
        self._config = None
        self._executor = None

    @property
    def executor(self):
        if not self._executor:
            self._executor = ExecutorSSH(self.addr[0], 22)
        return self._executor

    @property
    def myname(self):
        """
        is the main config
        """
        myname = MyEnv.sshagent.key_default_name
        c = self.config["clients"]
        if myname not in c:
            y = Tools.ask_yes_no("is our unique login name:%s\nif not please say no and define new name." % myname)
            if not y:
                myname2 = Tools.ask_string("give your unique loginname")
                msg = "careful: your sshkeyname will be changed accordingly on your system to:%s, ok?" % myname2
                if Tools.ask_yes_no(msg):
                    src = MyEnv.sshagent.key_path_get()
                    dest = "%s/%s" % (os.path.dirname(src), myname2)
                    shutil.copyfile(src, dest)
                    shutil.copyfile(src + ".pub", dest + ".pub")
                    MyEnv.config["SSH_KEY_DEFAULT"] = myname2
                    MyEnv.config_save()
                    Tools.delete(src)
                    Tools.delete(src + ".pub")
                    MyEnv.sshagent.keys_unload()
                    MyEnv.sshagent.key_load(dest)
                    myname = myname2
                else:
                    raise Tools.exceptions.Input(
                        "cannot continue need unique login name which corresponds to your sshkey"
                    )
            c[myname] = {}
        c = c[myname]
        keypub = MyEnv.sshagent.keypub

        def showdetails(c):
            print(json.dumps(c))

        def askdetails(c):

            organizations = ["codescalers", "freeflow", "frequencyvillage", "threefold", "incubaid", "bettertoken"]
            organizations2 = ", ".join(organizations)
            if "email" not in c:
                c["email"] = Tools.ask_string("please provide your main email addr")
            if "organizations" not in c:
                print("valid organizations: '%s'" % organizations2)
                c["organizations"] = Tools.ask_string("please provide your organizations (comma separated)")
            if "remark" not in c:
                c["remark"] = Tools.ask_string("any remark?")
            if "telegram" not in c:
                c["telegram"] = Tools.ask_string("please provide your main telegram handle")
            if "mobile" not in c:
                c["mobile"] = Tools.ask_string("please provide your mobile nr's (if more than one use ,)")
            showdetails(c)
            y = Tools.ask_yes_no("is above all correct !!!")
            if not y:
                c["email"] = Tools.ask_string("please provide your main email addr", default=c["email"])
                print("valid organizations: '%s'" % organizations2)
                c["organizations"] = Tools.ask_string(
                    "please provide your organizations (comma separated)", default=c["organizations"]
                )
                c["remark"] = Tools.ask_string("any remark?", default=c["remark"])
                c["telegram"] = Tools.ask_string("please provide your main telegram handle", default=c["telegram"])
                c["mobile"] = Tools.ask_string(
                    "please provide your mobile nr's (if more than one use ,)", default=c["mobile"]
                )
            self.executor.save()

            o = c["organizations"]
            o2 = []
            for oname in o.lower().split(","):
                oname = oname.strip().lower()
                if oname == "":
                    continue
                if oname not in organizations:
                    raise Tools.exceptions.Input(
                        "please choose valid organizations (notok:%s): %s" % (oname, organizations2)
                    )
                o2.append(oname)
            c["organizations"] = ",".join(o2)

        if "keypub" not in c:
            c["keypub"] = keypub
            askdetails()
            self.executor.save()
        else:
            if not c["keypub"].strip() == keypub.strip():
                showdetails(c)
                y = Tools.ask_yes_no("Are you sure your are above?")
                raise Tools.exceptions.Input(
                    "keypub does not correspond, your name:%s, is this a unique name, comes from your main sshkey, change if needed"
                    % myname
                )
        return myname

    def load(self):
        self._config = None

    @property
    def config_mine(self):
        return self.config["clients"][self.myname]

    @property
    def myid(self):
        if "myid" not in self.config_mine:
            if "lastmyid" not in self.config:
                self.config["lastmyid"] = 1
            else:
                self.config["lastmyid"] += 1
            self.config_mine["myid"] = self.config["lastmyid"]
            self.executor.save()
        return self.config_mine["myid"]

    # @iterator
    # def users(self):
    #     for name, data in self.config["clients"].items():
    #         yield data

    @property
    def config(self):
        """
        is the main config
        """
        if not self._config:
            c = self.executor.config
            if not "registry" in c:
                c["registry"] = {}
            config = self.executor.config["registry"]
            if "clients" not in config:
                config["clients"] = {}
            self._config = config
        return self._config


class WireGuardServer:
    """
    the server is over SSH, the one running this tool is the client
    and has access to local machine

    myid is unique id < 200
    the server id is always >200

    myid==199 means we are on local docker

    this is not a full blown client/server implementation for wireguard, its made for 1 server
    which we can access over ssh
    and multiple clients

    """

    def __init__(self, addr=None, port=22, myid=None):
        self._config = None
        assert addr
        self.addr = addr
        self.port = port
        self.port_wireguard = 9001

        if not myid:
            myid = MyEnv.registry.myid

        self.myid = myid
        self.serverid = 201

        assert myid != self.serverid
        assert self.serverid > 200

        self._config_local = None
        self.executor = ExecutorSSH(addr, port)

    def reset(self):
        """
        reset client and server
        """
        self.config["clients"].pop(self.myid)
        self.executor.config.pop("wireguard")
        # now makes sure is all empty on server
        self.executor.save()

    def install(self):
        ubuntu_install = """
            apt-get install software-properties-common -y
            add-apt-repository ppa:wireguard/wireguard
            apt-get update
            apt-get install wireguard -y
            """
        if not Tools.cmd_installed("wg"):
            if MyEnv.platform() == "linux":
                Tools.execute(ubuntu_install)
            elif MyEnv.platform() == "darwin":
                C = "brew install wireguard-tools bash"
                Tools.execute(C)
        if not self.executor.cmd_installed("wg"):
            # only ubuntu for now
            self.executor.execute(ubuntu_install, interactive=True)

    @property
    def config(self):
        c = self.executor.config
        if not "wireguard" in c:
            c["wireguard"] = {}
        wgconfig = self.executor.config["wireguard"]
        if "clients" not in wgconfig:
            wgconfig["clients"] = {}
        if self.myid not in wgconfig["clients"]:
            wgconfig["clients"][self.myid] = {}
        if "server" not in wgconfig:
            wgconfig["server"] = {}
        if "WIREGUARD_PORT" not in wgconfig["server"]:
            wgconfig["server"]["WIREGUARD_PORT"] = self.port_wireguard
            wgconfig["server"]["WIREGUARD_ADDR"] = self.addr
        if "serverid" not in wgconfig["server"]:
            wgconfig["server"]["serverid"] = self.serverid
        return wgconfig

    @property
    def config_server_mine(self):
        return self.config["clients"][self.myid]

    @property
    def config_server(self):
        return self.config["server"]

    @property
    def config_local(self):
        config_local = self.config_server_mine
        if "WIREGUARD_CLIENT_PRIVKEY" not in config_local:
            privkey, pubkey = self.generate_key_pair()
            config_local["WIREGUARD_CLIENT_PUBKEY"] = pubkey
            config_local["WIREGUARD_CLIENT_PRIVKEY"] = privkey
            self.save()
        return config_local

    def save(self):
        """
        everything always stored on server
        """
        self.executor.save()

    def generate_key_pair(self):
        print("- GENERATE WIREGUARD KEY")
        rc, out, err = Tools.execute("wg genkey", showout=False)
        privkey = out.strip()
        rc, out2, err = Tools.execute("echo %s | wg pubkey" % privkey, showout=False)
        pubkey = out2.strip()
        return privkey, pubkey

    def _subnet_calc(self, a):
        """
        go from integer to 2 bytes
        :return:
        """
        import struct

        s = struct.pack(">H", a)
        first, second = struct.unpack(">BB", s)

        return "%s.%s" % (first, second)

    def server_start(self):
        self.install()
        config = self.config["server"]
        if "WIREGUARD_SERVER_PUBKEY" not in config:
            privkey, pubkey = self.generate_key_pair()
            config["WIREGUARD_SERVER_PUBKEY"] = pubkey
            config["WIREGUARD_SERVER_PRIVKEY"] = privkey
            config["SUBNET"] = self._subnet_calc(self.serverid)
            # config["IP_ADDRESS"] = f'10.{config["SUBNET"]}.{ip_last_byte}/24'

        self.config_server_mine["WIREGUARD_CLIENT_PUBKEY"] = self.config_local["WIREGUARD_CLIENT_PUBKEY"]
        self.config_server_mine["SUBNET"] = self._subnet_calc(self.myid)

        self.save()

        C = """
        [Interface]
        Address = 10.{SUBNET}.1/24
        SaveConfig = true
        PrivateKey = {WIREGUARD_SERVER_PRIVKEY}
        ListenPort = {WIREGUARD_PORT}
        """
        C = Tools.text_replace(C, args=config, die_if_args_left=True)

        for client_id, client in self.config["clients"].items():
            C2 = """

            [Peer]
            PublicKey = {WIREGUARD_CLIENT_PUBKEY}
            AllowedIPs = 10.{SUBNET}.0/24
            """
            C2 = Tools.text_replace(C2, args=client, die_if_args_left=True)
            C += C2

        path = "/etc/wireguard/wg0.conf"
        self.executor.file_write(path, C, mode="0600")
        rc, out, err = self.executor.execute("ip link del dev wg0", showout=False, die=False)
        # cmd = "wg-quick down %s" % path #DONT DO BECAUSE OVERWRITES CONFIG
        # self.executor.execute(cmd)
        cmd = "wg-quick up %s" % path
        self.executor.execute(cmd)

    def connect(self):

        C = """
        [Interface]
        Address = 10.{SUBNET}.2/24
        PrivateKey = {WIREGUARD_CLIENT_PRIVKEY}
        """
        self.config_local["SUBNET"] = self._subnet_calc(self.myid)
        C = Tools.text_replace(C, args=self.config_local)
        C2 = """

        [Peer]
        PublicKey = {WIREGUARD_SERVER_PUBKEY}
        Endpoint = {WIREGUARD_ADDR}:{WIREGUARD_PORT}
        AllowedIPs = 10.{SUBNET}.0/24
        AllowedIPs = 172.17.0.0/16
        PersistentKeepalive = 25
        """
        C2 = Tools.text_replace(C2, args=self.config_server)
        C += C2
        Tools.file_write(self.config_path_client, C)
        self.disconnect()
        if MyEnv.platform() == "linux":
            cmd = "/usr/local/bin/bash /usr/local/bin/wg-quick up %s" % self.config_path_client
            Tools.execute(cmd)
            Tools.shell()
        else:
            cmd = "/usr/local/bin/bash /usr/local/bin/wg-quick up %s" % self.config_path_client
            print(cmd)
            Tools.execute(cmd)

    @property
    def config_path_client(self):
        path = "{DIR_BASE}/cfg/wireguard/%s/wg0.conf" % self.serverid
        path = Tools.text_replace(path)
        Tools.dir_ensure(os.path.dirname(path))
        return path

    def disconnect(self):
        """
        stop the client
        """
        if MyEnv.platform() == "linux":
            rc, out, err = Tools.execute("ip link del dev wg0", showout=False, die=False)
        else:
            cmd = "/usr/local/bin/bash /usr/local/bin/wg-quick down %s" % self.config_path_client
            Tools.execute(cmd, die=False, showout=True)

    @property
    def config_file_server(self):
        path = "/etc/wireguard/wg0.conf"
        return str(self.executor.file_read(path))

    @property
    def config_file_client(self):
        path = "{DIR_BASE}/cfg/wireguard/%s/wg0.conf" % self.serverid
        path = Tools.text_replace(path)

        return str(Tools.file_read(path).decode())

    def __repr__(self):
        out = ""
        out += self.config_file_server
        out += "\n\n====================================CLIENT======================\n"
        out += self.config_file_client
        return out

    __str__ = __repr__


MyEnv.init()
MyEnv.registry = Registry()
