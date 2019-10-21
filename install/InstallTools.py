from __future__ import unicode_literals
import getpass
import pickle
import re

DEFAULT_BRANCH = "development"
GITREPOS = {}

GITREPOS["builders_extra"] = [
    "https://github.com/threefoldtech/jumpscaleX_builders",
    "%s" % DEFAULT_BRANCH,
    "JumpscaleBuildersExtra",
    "{DIR_BASE}/lib/jumpscale/JumpscaleBuildersExtra",
]


GITREPOS["installer"] = [
    "https://github.com/threefoldtech/jumpscaleX_core",
    "%s" % DEFAULT_BRANCH,
    "install",  # directory in the git repo
    "{DIR_BASE}/installer",
]
GITREPOS["core"] = [
    "https://github.com/threefoldtech/jumpscaleX_core",
    "%s" % DEFAULT_BRANCH,
    "JumpscaleCore",
    "{DIR_BASE}/lib/jumpscale/Jumpscale",
]
GITREPOS["home"] = ["https://github.com/threefoldtech/home", "master", "", "{DIR_BASE}/lib/jumpscale/home"]

GITREPOS["builders"] = [
    "https://github.com/threefoldtech/jumpscaleX_builders",
    "%s" % DEFAULT_BRANCH,
    "JumpscaleBuilders",
    "{DIR_BASE}/lib/jumpscale/JumpscaleBuilders",
]

GITREPOS["builders_community"] = [
    "https://github.com/threefoldtech/jumpscaleX_builders",
    "%s" % DEFAULT_BRANCH,
    "JumpscaleBuildersCommunity",
    "{DIR_BASE}/lib/jumpscale/JumpscaleBuildersCommunity",
]


GITREPOS["libs_extra"] = [
    "https://github.com/threefoldtech/jumpscaleX_libs_extra",
    "%s" % DEFAULT_BRANCH,
    "JumpscaleLibsExtra",
    "{DIR_BASE}/lib/jumpscale/JumpscaleLibsExtra",
]
GITREPOS["libs"] = [
    "https://github.com/threefoldtech/jumpscaleX_libs",
    "%s" % DEFAULT_BRANCH,
    "JumpscaleLibs",
    "{DIR_BASE}/lib/jumpscale/JumpscaleLibs",
]
GITREPOS["threebot"] = [
    "https://github.com/threefoldtech/jumpscaleX_threebot",
    "%s" % DEFAULT_BRANCH,
    "ThreeBotPackages",
    "{DIR_BASE}/lib/jumpscale/threebot_packages",
]

GITREPOS["tutorials"] = [
    "https://github.com/threefoldtech/jumpscaleX_libs",
    "%s" % DEFAULT_BRANCH,
    "tutorials",
    "{DIR_BASE}/lib/jumpscale/tutorials",
]

GITREPOS["kosmos"] = [
    "https://github.com/threefoldtech/jumpscaleX_threebot",
    "%s" % DEFAULT_BRANCH,
    "kosmos",
    "{DIR_BASE}/lib/jumpscale/kosmos",
]

PREBUILT_REPO = ["https://github.com/threefoldtech/sandbox_threebot_linux64", "master", "", "not used"]

import socket
import grp
import os
import random
import shutil
import stat
import subprocess
import sys
import textwrap
import time
import re
import inspect
import json
from fcntl import F_GETFL, F_SETFL, fcntl
from os import O_NONBLOCK
from pathlib import Path
from subprocess import Popen

try:
    import traceback
except:
    traceback = None

try:
    import pudb
except:
    pudb = None

try:
    import pygments
except Exception as e:
    pygments = None

if pygments:
    from pygments import formatters
    from pygments import lexers

    pygments_formatter = formatters.get_formatter_by_name("terminal")
    pygments_pylexer = lexers.get_lexer_by_name("python")
else:
    pygments_formatter = False
    pygments_pylexer = False


# try:
#     import colored_traceback
#     colored_traceback.add_hook(always=True)
# except ImportError:
#     pass
#


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
        except Exception as e:
            # print("WARNING: COULD NOT YAML SERIALIZE")
            # return str(data)
            data = "CANNOT SERIALIZE YAML"
        return data


except:
    try:
        def serializer(data):
            if hasattr(data, "_data"):
                return str(data._data)
            if hasattr(data, "_ddict"):
                data = data._ddict
            try:
                return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=True)
            except Exception as e:
                # data = str(data)
                data = "CANNOT SERIALIZE"
                return data

    except:

        def serializer(data):
            return "CANNOT SERIALIZE"


class RedisTools:
    @staticmethod
    def client_core_get(
        addr="localhost", port=6379, unix_socket_path="{DIR_BASE}/var/redis.sock", die=True, fake_ok=True
    ):
        """

        :param addr:
        :param port:
        :param unix_socket_path:
        :param die: if cannot find fake or real die
        :param fake_ok: can return a fake redis connection which will go to memory only
        :return:
        """

        RedisTools.unix_socket_path = unix_socket_path

        try:
            import redis
        except ImportError:
            if fake_ok:
                try:
                    import fakeredis

                    res = fakeredis.FakeStrictRedis()
                    res.fake = True
                    return res
                except ImportError:
                    # dit not find fakeredis so can only return None
                    if die:
                        raise Tools.exceptions.Base(
                            "cannot connect to fakeredis, could not import the library, please install fakeredis"
                        )
                    return None
            else:
                if die:
                    raise Tools.exceptions.Base("redis python lib not installed, do pip3 install redis")
                return None

        try:
            cl = Redis(unix_socket_path=unix_socket_path, db=0)
            cl.fake = False
            assert cl.ping()
        except Exception as e:
            cl = None
            if addr == "" and die:
                raise e
        else:
            return cl

        try:
            cl = Redis(host=addr, port=port, db=0)
            cl.fake = False
            assert cl.ping()
        except Exception as e:
            if die:
                raise e
            cl = None

        return cl

    @staticmethod
    def core_get(reset=False, tcp=True):
        """

        kosmos 'j.clients.redis.core_get(reset=False)'

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

        if reset:
            RedisTools.core_stop()

        MyEnv.init()

        if MyEnv.db and MyEnv.db.ping() and MyEnv.db.fake is False:
            return MyEnv.db

        if not RedisTools.core_running(tcp=tcp):
            RedisTools._core_start(tcp=tcp)

        MyEnv.db = RedisTools.client_core_get()

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
            r = RedisTools.client_core_get(fake_ok=False, die=False)
            if r:
                return True

        if tcp and Tools.tcp_port_connection_test("localhost", 6379):
            r = RedisTools.client_core_get(ipaddr="localhost", port=6379, fake_ok=False, die=False)
            if r:
                return True

        return False

    def _core_start(tcp=True, timeout=20, reset=False):

        """
        kosmos "j.clients.redis.core_get(reset=True)"

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

        if reset == False:
            if RedisTools.core_running(tcp=tcp):
                return RedisTools.core_get()

            if MyEnv.platform_is_osx:
                if not Tools.cmd_installed("redis-server"):
                    # prefab.system.package.install('redis')
                    Tools.execute("brew unlink redis", die=False)
                    Tools.execute("brew install redis")
                    Tools.execute("brew link redis")
                    if not Tools.cmd_installed("redis-server"):
                        raise Tools.exceptions.Base("Cannot find redis-server even after install")
                Tools.execute("redis-cli -s {DIR_TMP}/redis.sock shutdown", die=False, showout=False)
                Tools.execute("redis-cli -s %s shutdown" % RedisTools.unix_socket_path, die=False, showout=False)
                Tools.execute("redis-cli shutdown", die=False, showout=False)
            elif MyEnv.platform_is_linux:
                Tools.execute("apt-get install redis-server -y")
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

        Tools.log(cmd)
        Tools.execute(cmd, replace=True)
        limit_timeout = time.time() + timeout
        while time.time() < limit_timeout:
            if RedisTools.core_running():
                break
            print(1)
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
            while self.empty == False:
                if self.get_nowait() == None:
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
        return Tools._data_serializer_safe(self.logdict)

    def __repr__(self):
        if not self.logdict:
            raise Tools.exceptions.JSBUG("logdict not known (is None)")
        print(Tools.log2str(self.logdict))
        return ""

    # def trace_print(self):
    #     j.core.errorhandler._trace_print(self._trace)


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


class OurTextFormatter(Formatter):
    def check_unused_args(self, used_args, args, kwargs):
        return used_args, args, kwargs


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
                        w
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
        stdout=True,
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
            - INFO 	    20
            - STDOUT 	15
            - DEBUG 	10


        :param _levelup 0, if e.g. 1 means will go 1 level more back in finding line nr where log comes from
        :param source, if you don't want to show the source (line nr in log), somewhat faster
        :param stdout: return as logdict or send to stdout
        :param: replace to replace the color variables for stdout
        :param: exception is jumpscale/python exception

        :return:
        """
        logdict = {}

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
            if cat is "":
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

        logdict["message"] = Tools.text_replace(msg)

        logdict["linenr"] = linenr
        logdict["filepath"] = fname
        logdict["processid"] = MyEnv.appname
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
            Tools.log2stdout(logdict, data_show=data_show)

        iserror = tb or exception
        return Tools.process_logdict_for_handlers(logdict, iserror)

    @staticmethod
    def process_logdict_for_handlers(logdict, iserror=True):
        """

        :param logdict:
        :param iserror:   if error will use MyEnv.errorhandlers: allways MyEnv.loghandlers
        :return:
        """

        # assert isinstance(logdict, dict)

        if iserror:
            for handler in MyEnv.errorhandlers:
                handler(logdict)

        for handler in MyEnv.loghandlers:
            try:
                handler(logdict)
            except Exception as e:
                MyEnv.exception_handle(e)

        # assert isinstance(logdict, dict)

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
            if line.startswith("def "):
                methodname = line.split("(", 1)[0].strip().replace("def ", "")

        if methodname == "":
            raise j.exceptions.Base("defname cannot be empty")

        return methodname, code3

    @staticmethod
    def _execute(command, die=True, env=None, cwd=None, useShell=True, async_=False, showout=True, timeout=3600):

        os.environ["PYTHONUNBUFFERED"] = "1"  # WHY THIS???

        # if hasattr(subprocess, "_mswindows"):
        #     mswindows = subprocess._mswindows
        # else:
        #     mswindows = subprocess.mswindows

        if env == None or env == {}:
            env = os.environ

        if useShell:
            p = Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=MyEnv.platform_is_unix,
                shell=True,
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

        if rc < 0 or rc > 0:
            if MyEnv.debug or showout:
                Tools.log("system.process.run ended, exitcode was %d" % rc)
        # if out!="":
        #     Tools.log('system.process.run stdout:\n%s' % out)
        # if err!="":
        #     Tools.log('system.process.run stderr:\n%s' % err)

        if die and rc != 0:
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

        # close the files (otherwise resources get lost),
        # wait for the process to die, and del the Popen object
        p.stdin.close()
        p.stderr.close()
        p.stdout.close()
        p.wait()
        del p

        return (rc, out, err)

    @staticmethod
    def _execute_interactive(cmd=None, args=None, die=True, original_command=None):

        if args is None:
            args = cmd.split(" ")
        # else:
        #     args[0] = shutil.which(args[0])

        returncode = os.spawnlp(os.P_WAIT, args[0], *args)
        cmd = " ".join(args)
        if returncode == 127:
            raise Tools.exceptions.Base("{}: command not found\n".format(cmd))
        if returncode > 0 and returncode != 999:
            if die:
                if original_command:
                    raise Tools.exceptions.Base(
                        "***ERROR EXECUTE INTERACTIVE:\nCould not execute:%s\nreturncode:%s\n"
                        % (original_command, returncode)
                    )
                else:
                    raise Tools.exceptions.Base(
                        "***ERROR EXECUTE INTERACTIVE:\nCould not execute:%s\nreturncode:%s\n" % (cmd, returncode)
                    )
            return returncode, "", ""
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
            p.write_text(content)
        else:
            p.write_bytes(content)

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

        if executor and executor.config:
            content2 = Tools.args_replace(
                content,
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
            if val == None:
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
    def log2stdout(logdict, data_show=True):
        def show():
            # always show in debugmode and critical
            if MyEnv.debug or logdict["level"] >= 50:
                return True
            if not MyEnv.log_console:
                return False
            return logdict["level"] >= MyEnv.log_loglevel

        if not show():
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
    def traceback_format(tb):
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
            timetuple = time.localtime(logdict)
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
        return Tools.text_replace("/tmp/jumpscale/scripts/{RANDOM}.{ext}", args={"RANDOM": Tools._random(), "ext": ext})

    @staticmethod
    def _random():
        return str(random.getrandbits(16))

    @staticmethod
    def get_envars():
        envars = dict()
        content = j.tools.executor.local.file_read("/proc/1/environ").strip("\x00").split("\x00")
        for item in content:
            k, v = item.split("=")
            envars[k] = v
        return envars

    @staticmethod
    def execute(
        command,
        showout=True,
        useShell=True,
        cwd=None,
        timeout=1800,
        die=True,
        async_=False,
        args=None,
        env=None,
        interactive=False,
        self=None,
        replace=True,
        asfile=False,
        original_command=None,
        log=False,
        sudo_remove=False,
        retry=None,
        errormsg=None,
        die_if_args_left=False,
    ):
        """

        :param command:
        :param showout:
        :param useShell:
        :param cwd:
        :param timeout:
        :param die:
        :param async_:
        :param args:
        :param env:
        :param interactive:
        :param self:
        :param replace:
        :param asfile:
        :param original_command:
        :param log:
        :param sudo_remove:
        :param retry:
        :param errormsg:
        :param die_if_args_left: it True will search for { if found after replace will die
        :return:
        """

        if env is None:
            env = {}
        if not retry:
            retry = 1
        if self is None:
            self = MyEnv
        command = Tools.text_strip(command, args=args, replace=replace)
        if die_if_args_left and "{" in command:
            raise j.exceptions.Input("Found { in %s" % command)
        if sudo_remove:
            command = command.replace("sudo ", "")

        if "\n" in command or asfile:
            path = Tools._file_path_tmp_get()
            if MyEnv.debug or log:
                Tools.log("execbash:\n'''%s\n%s'''\n" % (path, command))
            command2 = ""
            if die:
                command2 = "set -e\n"
            if cwd:
                command2 += "cd %s\n" % cwd
            command2 += command
            Tools.file_write(path, command2)
            # print(command2)
            command3 = "bash %s" % path
            res = Tools.execute(
                command3,
                showout=showout,
                useShell=useShell,
                cwd=cwd,
                timeout=timeout,
                die=die,
                env=env,
                self=self,
                interactive=interactive,
                asfile=False,
                original_command=command,
            )
            Tools.delete(path)
            return res
        else:

            if interactive:
                rc = 1
                counter = 0
                if MyEnv.debug or log:
                    Tools.log("execute interactive:%s" % command)
                while rc > 0 and counter < retry:
                    rc, out, err = Tools._execute_interactive(cmd=command, die=False, original_command=original_command)
                    counter += 1
                if die and rc > 0:
                    raise Tools.exceptions.Base("Could not execute:%s" % command)
                return rc, out, err
            else:
                if MyEnv.debug or log:
                    Tools.log("execute:%s" % command)

                rc = 1
                counter = 0
                while rc > 0 and counter < retry:
                    rc, out, err = Tools._execute(
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

    # @staticmethod
    # def run(script,die=True,args={},interactive=True,showout=True):
    #     if "\n" in script:
    #         script = Tools.text_strip(script,args=args)
    #         if showout:
    #             if "\n" in script:
    #                 Tools.log("RUN:\n%s"%script)
    #             else:
    #                 Tools.log("RUN: %s"%script)
    #         path_script = "/tmp/jumpscale/run_script.sh"
    #         p = Path(path_script)
    #         p.write_text(script)
    #         return Tools._execute("bash %s"%path_script,die=die,interactive=interactive,showout=showout)
    #     else:
    #         return Tools._execute(cmd=script, args=None, die=die, interactive=interactive, showout=showout)
    #

    @staticmethod
    def system_cleanup():
        print("- AM CLEANING UP THE CONTAINER, THIS TAKES A WHILE")
        CMD = BaseInstaller.cleanup_script_get()
        for line in CMD.split("\n"):
            Tools.execute(line, replace=False)

    @staticmethod
    def process_pids_get_by_filter(filterstr, excludes=[]):
        cmd = "ps ax | grep '%s'" % filterstr
        rcode, out, err = Tools.execute(cmd)
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
    def process_kill_by_by_filter(filterstr):
        for pid in Tools.process_pids_get_by_filter(filterstr):
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
    def ask_password(question="give secret", confirm=True, regex=None, retry=-1, validate=None):
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
    def _code_location_get(account, repo):
        """
        accountdir will be created if it does not exist yet
        :param repo:
        :param static: static means we don't use git

        :return: repodir_exists,foundgit, accountdir,repodir

            foundgit means, we found .git in the repodir
            dontpull means, we found .dontpull in the repodir, means code is being synced to the repo from remote, should not update

        """

        prefix = "code"
        if "DIR_CODE" in MyEnv.config:
            accountdir = os.path.join(MyEnv.config["DIR_CODE"], "github", account)
        else:
            accountdir = os.path.join(MyEnv.config["DIR_BASE"], prefix, "github", account)
        repodir = os.path.join(accountdir, repo)
        gitdir = os.path.join(repodir, ".git")
        dontpullloc = os.path.join(repodir, ".dontpull")
        if os.path.exists(accountdir):
            if os.listdir(accountdir) == []:
                shutil.rmtree(accountdir)  # lets remove the dir & return it does not exist

        exists = os.path.exists(repodir)
        foundgit = os.path.exists(gitdir)
        dontpull = os.path.exists(dontpullloc)
        return exists, foundgit, dontpull, accountdir, repodir

    @staticmethod
    def code_changed(path):
        """
        check if there is code in there which changed
        :param path:
        :return:
        """
        S = """
        cd {REPO_DIR}
        git diff --exit-code || exit 1
        git diff --cached --exit-code || exit 1
        if git status --porcelain | grep .; then
            exit 1
        else
            exit 0
        fi
        """
        args = {}
        args["REPO_DIR"] = path
        rc, out, err = Tools.execute(S, showout=False, die=False, args=args)
        return rc > 0

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

        return protocol, repository_host, repository_account, repository_name, repository_url, port

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

        protocol, repository_host, repository_account, repository_name, repository_url, port = Tools.code_git_rewrite_url(
            url=url, login=login, passwd=passwd, ssh=ssh
        )

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
        repository_host, repository_type, repository_account, repository_name, repository_url, port = Tools.code_git_rewrite_url(
            url=url
        )
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
    def code_github_get(url, rpath=None, branch=None, pull=False, reset=False):
        """

        :param repo:
        :param account:
        :param branch: falls back to the default branch on MyEnv.DEFAULT_BRANCH
                    if needed, when directory exists and pull is False will not check branch
        :param pull:
        :param reset:
        :return:
        """

        def getbranch(args):
            cmd = "cd {REPO_DIR}; git branch | grep \* | cut -d ' ' -f2"
            rc, stdout, err = Tools.execute(cmd, die=False, args=args, interactive=False, die_if_args_left=True)
            if rc > 0:
                Tools.shell()
            current_branch = stdout.strip()
            Tools.log("Found branch: %s" % current_branch)
            return current_branch

        def checkoutbranch(args, branch):
            args["BRANCH"] = branch
            current_branch = getbranch(args=args)
            if current_branch != branch:
                script = """
                set -ex
                cd {REPO_DIR}
                git checkout {BRANCH} -f
                """
                rc, out, err = Tools.execute(
                    script, die=False, args=args, showout=True, interactive=False, die_if_args_left=True
                )
                # if err:
                #     script = """
                #     set -ex
                #     cd {REPO_DIR}
                #     git checkout {BRANCH} -f
                #     """
                #     rc, out, err = Tools.execute(script, die=False, args=args, showout=True, interactive=False)

                if rc > 0:
                    return False

            return True

        (host, type, account, repo, url2, branch2, gitpath, path, port) = Tools.code_giturl_parse(url=url)
        if rpath:
            path = rpath
        assert "/" not in repo

        if branch is None:
            branch = branch2
        elif isinstance(branch, str):
            if "," in branch:
                raise j.exceptions.JSBUG("no support for multiple branches yet")
                branch = [branch.strip() for branch in branch.split(",")]
        elif isinstance(branch, (set, list)):
            raise j.exceptions.JSBUG("no support for multiple branches yet")
            branch = [branch.strip() for branch in branch]
        else:
            raise Tools.exceptions.JSBUG("branch should be a string or list, now %s" % branch)

        Tools.log("get code:%s:%s (%s)" % (url, path, branch))
        if MyEnv.config["SSH_AGENT"] and MyEnv.interactive:
            url = "git@github.com:%s/%s.git"
        else:
            url = "https://github.com/%s/%s.git"

        repo_url = url % (account, repo)
        exists, foundgit, dontpull, ACCOUNT_DIR, REPO_DIR = Tools._code_location_get(account=account, repo=repo)

        if reset:
            Tools.delete(REPO_DIR)
            exists, foundgit, dontpull, ACCOUNT_DIR, REPO_DIR = Tools._code_location_get(account=account, repo=repo)

        args = {}
        args["ACCOUNT_DIR"] = ACCOUNT_DIR
        args["REPO_DIR"] = REPO_DIR
        args["URL"] = repo_url
        args["NAME"] = repo

        args["BRANCH"] = branch  # TODO:no support for multiple branches yet

        if "GITPULL" in os.environ:
            pull = str(os.environ["GITPULL"]) == "1"

        git_on_system = Tools.cmd_installed("git")

        if exists and not foundgit and not pull:
            """means code is already there, maybe synced?"""
            return gitpath

        if git_on_system and MyEnv.config["USEGIT"] and ((exists and foundgit) or not exists):
            # there is ssh-key loaded
            # or there is a dir with .git inside and exists
            # or it does not exist yet
            # then we need to use git

            C = ""

            if exists is False:
                C = """
                set -e
                mkdir -p {ACCOUNT_DIR}
                """
                Tools.log("get code [git] (first time): %s" % repo)
                Tools.execute(C, args=args, showout=False, die_if_args_left=True)
                C = """
                cd {ACCOUNT_DIR}
                # git clone  --depth 1 {URL} -b {BRANCH}
                git clone {URL} -b {BRANCH}
                cd {NAME}
                """
                rc, out, err = Tools.execute(
                    C,
                    args=args,
                    die=True,
                    showout=False,
                    retry=4,
                    errormsg="Could not clone %s" % repo_url,
                    die_if_args_left=True,
                )

            else:
                if pull:
                    if reset:
                        C = """
                        set -x
                        cd {REPO_DIR}
                        git checkout . --force
                        """
                        Tools.log("get code & ignore changes: %s" % repo)
                        Tools.execute(
                            C, args=args, retry=1, errormsg="Could not checkout %s" % repo_url, die_if_args_left=True
                        )
                        C = """
                        set -x
                        cd {REPO_DIR}
                        git pull
                        """
                        Tools.log("get code & ignore changes: %s" % repo)
                        Tools.execute(
                            C, args=args, retry=4, errormsg="Could not pull %s" % repo_url, die_if_args_left=True
                        )

                    elif Tools.code_changed(REPO_DIR):
                        if Tools.ask_yes_no("\n**: found changes in repo '%s', do you want to commit?" % repo):
                            if "GITMESSAGE" in os.environ:
                                args["MESSAGE"] = os.environ["GITMESSAGE"]
                            else:
                                args["MESSAGE"] = input("\nprovide commit message: ")
                                assert args["MESSAGE"].strip() != ""
                        else:
                            raise Tools.exceptions.Input("found changes, do not want to commit")
                        C = """
                        set -x
                        cd {REPO_DIR}
                        git add . -A
                        git commit -m "{MESSAGE}"
                        """
                        Tools.log("get code & commit [git]: %s" % repo)
                        Tools.execute(C, args=args, die_if_args_left=True)
                        C = """
                        set -x
                        cd {REPO_DIR}
                        git pull
                        """
                        Tools.log("get code & commit [git]: %s" % repo)
                        Tools.execute(
                            C, args=args, retry=4, errormsg="Could not pull %s" % repo_url, die_if_args_left=True
                        )

                    if not checkoutbranch(args, branch):
                        raise Tools.exceptions.Input("Could not checkout branch:%s on %s" % (branch, args["REPO_DIR"]))

        else:
            Tools.log("get code [zip]: %s" % repo)
            args = {}
            args["ACCOUNT_DIR"] = ACCOUNT_DIR
            args["REPO_DIR"] = REPO_DIR
            args["URL"] = "https://github.com/%s/%s/archive/%s.zip" % (account, repo, branch)
            args["NAME"] = repo
            args["BRANCH"] = branch.strip()

            script = """
            set -ex
            cd {DIR_TEMP}
            rm -f download.zip
            curl -L {URL} > download.zip
            """
            Tools.execute(
                script, args=args, retry=3, errormsg="Cannot download:%s" % args["URL"], die_if_args_left=True
            )
            statinfo = os.stat("/tmp/jumpscale/download.zip")
            if statinfo.st_size < 100000:
                raise Tools.exceptions.Operations("cannot download:%s resulting file was too small" % args["URL"])
            else:
                script = """
                set -ex
                cd {DIR_TEMP}
                rm -rf {NAME}-{BRANCH}
                mkdir -p {REPO_DIR}
                rm -rf {REPO_DIR}
                unzip download.zip > /tmp/unzip
                mv {NAME}-{BRANCH} {REPO_DIR}
                rm -f download.zip
                """
                try:
                    Tools.execute(script, args=args, die=True, die_if_args_left=True)
                except Exception as e:
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
            elif val == True:
                val = "true"
            elif val == False:
                val = "false"
            out += "%s = %s\n" % (key, val)

        if executor:
            executor.file_write(path, out)
        else:
            Tools.file_write(path, out)


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
        self.log_console = True
        self.log_loglevel = 15

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

        LOGFORMATBASE = (
            "{COLOR}{TIME} {filename:<20}{RESET} -{linenr:4d} - {GRAY}{context:<35}{RESET}: {message}"
        )  # DO NOT CHANGE COLOR

        self.LOGFORMAT = {
            "DEBUG": LOGFORMATBASE.replace("{COLOR}", "{CYAN}"),
            "STDOUT": "{message}",
            # 'INFO': '{BLUE}* {message}{RESET}',
            "INFO": LOGFORMATBASE.replace("{COLOR}", "{BLUE}"),
            "WARNING": LOGFORMATBASE.replace("{COLOR}", "{YELLOW}"),
            "ERROR": LOGFORMATBASE.replace("{COLOR}", "{RED}"),
            "CRITICAL": "{RED}{TIME} {filename:<20} -{linenr:4d} - {GRAY}{context:<35}{RESET}: {message}",
        }

        self.db = RedisTools.client_core_get(die=False)

    def init(self, reset=False, configdir=None):

        args = Tools.cmd_args_get()

        if self.platform() == "linux":
            self.platform_is_linux = True
            self.platform_is_unix = True
            self.platform_is_osx = False
        elif "darwin" in self.platform():
            self.platform_is_linux = False
            self.platform_is_unix = True
            self.platform_is_osx = True
        else:
            raise Tools.exceptions.Base("platform not supported, only linux or osx for now.")

        if not configdir:
            if "JSX_DIR_CFG" in os.environ:
                configdir = os.environ["JSX_DIR_CFG"]
            else:
                if configdir is None and "configdir" in args:
                    configdir = args["configdir"]
                else:
                    configdir = self._cfgdir_get()

        self.config_file_path = os.path.join(configdir, "jumpscale_config.toml")
        # if DockerFactory.indocker():
        #     # this is important it means if we push a container we keep the state file
        #     self.state_file_path = os.path.join(self._homedir_get(), ".jumpscale_done.toml")
        # else:
        self.state_file_path = os.path.join(configdir, "jumpscale_done.toml")

        if Tools.exists(self.config_file_path):
            self._config_load()
            if not "DIR_BASE" in self.config:
                return

            self.log_includes = [i for i in self.config.get("LOGGER_INCLUDE", []) if i.strip().strip("''") != ""]
            self.log_excludes = [i for i in self.config.get("LOGGER_EXCLUDE", []) if i.strip().strip("''") != ""]
            self.log_loglevel = self.config.get("LOGGER_LEVEL", 50)
            self.log_console = self.config.get("LOGGER_CONSOLE", True)
            self.log_redis = self.config.get("LOGGER_REDIS", False)
            self.debug = self.config.get("DEBUG", False)
            self.debugger = self.config.get("DEBUGGER", "pudb")
            self.interactive = self.config.get("INTERACTIVE", True)

            if os.path.exists(os.path.join(self.config["DIR_BASE"], "bin", "python3.6")):
                self.sandbox_python_active = True
            else:
                self.sandbox_python_active = False

        else:
            self.config = self.config_default_get()

        self._state_load()

        if self.config["SSH_AGENT"]:
            self.sshagent = SSHAgent()

        sys.excepthook = self.excepthook

        self.__init = True

    def _init(self, **kwargs):
        if not self.__init:
            raise RuntimeError("init on MyEnv did not happen yet")

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
        isroot = None
        rc, out, err = Tools.execute("whoami", showout=False, die=False)
        if rc == 0:
            if out.strip() == "root":
                isroot = 1
        if Tools.exists("/sandbox") or isroot == 1:
            Tools.dir_ensure("/sandbox")
            return "/sandbox"
        p = "%s/sandbox" % self._homedir_get()
        if not Tools.exists(p):
            Tools.dir_ensure(p)
        return p

    def _cfgdir_get(self):
        if self.readonly:
            return "/tmp/jumpscale/cfg"
        return "%s/cfg" % self._basedir_get()

    def config_default_get(self, config={}):
        if "DIR_BASE" not in config:
            config["DIR_BASE"] = self._basedir_get()

        if "DIR_HOME" not in config:
            config["DIR_HOME"] = self._homedir_get()

        if not "DIR_CFG" in config:
            config["DIR_CFG"] = self._cfgdir_get()

        if not "USEGIT" in config:
            config["USEGIT"] = True
        if not "READONLY" in config:
            config["READONLY"] = False
        if not "DEBUG" in config:
            config["DEBUG"] = False
        if not "DEBUGGER" in config:
            config["DEBUGGER"] = "pudb"
        if not "INTERACTIVE" in config:
            config["INTERACTIVE"] = True
        if not "SECRET" in config:
            config["SECRET"] = ""
        if "SSH_AGENT" not in config:
            config["SSH_AGENT"] = True
        if "SSH_KEY_DEFAULT" not in config:
            config["SSH_KEY_DEFAULT"] = ""
        if "LOGGER_INCLUDE" not in config:
            config["LOGGER_INCLUDE"] = ["*"]
        if "LOGGER_EXCLUDE" not in config:
            config["LOGGER_EXCLUDE"] = ["sal.fs"]
        if "LOGGER_LEVEL" not in config:
            config["LOGGER_LEVEL"] = 15  # means std out & plus gets logged
        if config["LOGGER_LEVEL"] > 50:
            config["LOGGER_LEVEL"] = 50
        if "LOGGER_CONSOLE" not in config:
            config["LOGGER_CONSOLE"] = True
        if "LOGGER_REDIS" not in config:
            config["LOGGER_REDIS"] = False
        if "LOGGER_PANEL_NRLINES" not in config:
            config["LOGGER_PANEL_NRLINES"] = 15

        if self.readonly:
            config["DIR_TEMP"] = "/tmp/jumpscale_installer"
            config["LOGGER_REDIS"] = False
            config["LOGGER_CONSOLE"] = True

        if not "DIR_TEMP" in config:
            config["DIR_TEMP"] = "/tmp/jumpscale"
        if not "DIR_VAR" in config:
            config["DIR_VAR"] = "%s/var" % config["DIR_BASE"]
        if not "DIR_CODE" in config:
            config["DIR_CODE"] = "%s/code" % config["DIR_BASE"]
            # if Tools.exists("%s/code" % config["DIR_BASE"]):
            #     config["DIR_CODE"] = "%s/code" % config["DIR_BASE"]
            # else:
            #     config["DIR_CODE"] = "%s/code" % config["DIR_HOME"]
        if not "DIR_BIN" in config:
            config["DIR_BIN"] = "%s/bin" % config["DIR_BASE"]
        if not "DIR_APPS" in config:
            config["DIR_APPS"] = "%s/apps" % config["DIR_BASE"]

        return config

    def configure(
        self,
        configdir=None,
        codedir=None,
        config={},
        readonly=None,
        sshkey=None,
        sshagent_use=None,
        debug_configure=None,
        secret=None,
        interactive=False,
    ):
        """

        the args of the command line will also be parsed, will check for

        --configdir=                    default $BASEDIR/cfg
        --codedir=                      default $BASEDIR/code

        --sshkey=                       key to use for ssh-agent if any
        --no-sshagent                   default is to use the sshagent, if you want to disable use this flag

        --readonly                      default is false
        --no-interactive                default is interactive, means will ask questions
        --debug_configure               default debug_configure is False, will configure in debug mode

        :param configdir: is the directory where all configuration & keys will be stored
        :param basedir: the root of the sandbox
        :param config: configuration arguments which go in the config file
        :param readonly: specific mode of operation where minimal changes will be done while using JSX
        :param codedir: std $sandboxdir/code
        :param sshkey: name of the sshkey to use if there are more than 1 in ssh-agent
        :param sshagent_use: needs to be True if sshkey used
        :return:
        """

        basedir = self._basedir_get()

        if not os.path.exists(self.config_file_path):
            self.config = self.config_default_get(config=config)
        else:
            self._config_load()

        if interactive not in [True, False]:
            raise Tools.exceptions.Base("interactive is True or False")
        args = Tools.cmd_args_get()

        if configdir is None and "configdir" in args:
            configdir = args["configdir"]
        if codedir is None and "codedir" in args:
            codedir = args["codedir"]
        if sshkey is None and "sshkey" in args:
            sshkey = args["sshkey"]

        if readonly is None and "readonly" in args:
            readonly = True

        if sshagent_use is None or ("no_sshagent" in args and sshagent_use is False):
            sshagent_use = False
        else:
            sshagent_use = True
        if debug_configure is None and "debug_configure" in args:
            debug_configure = True

        if not configdir:
            if "DIR_CFG" in config:
                configdir = config["DIR_CFG"]
            elif "JSX_DIR_CFG" in os.environ:
                configdir = os.environ["JSX_DIR_CFG"]
            else:
                configdir = self._cfgdir_get()
        config["DIR_CFG"] = configdir

        # installpath = os.path.dirname(inspect.getfile(os.path))
        # # MEI means we are pyexe BaseInstaller
        # if installpath.find("/_MEI") != -1 or installpath.endswith("dist/install"):
        #     pass  # dont need yet but keep here

        config["DIR_BASE"] = basedir

        if basedir == "/sandbox" and not os.path.exists(basedir):
            script = """
            set -ex
            cd /
            sudo mkdir -p {DIR_BASE}/cfg
            sudo chown -R {USERNAME}:{GROUPNAME} {DIR_BASE}
            mkdir -p /usr/local/EGG-INFO
            sudo chown -R {USERNAME}:{GROUPNAME} /usr/local/EGG-INFO
            """
            args = {}
            args["DIR_BASE"] = basedir
            args["USERNAME"] = getpass.getuser()
            st = os.stat(self.config["DIR_HOME"])
            gid = st.st_gid
            args["GROUPNAME"] = grp.getgrgid(gid)[0]
            Tools.execute(script, interactive=True, args=args, die_if_args_left=True)

        self.config_file_path = os.path.join(config["DIR_CFG"], "jumpscale_config.toml")

        if codedir is not None:
            config["DIR_CODE"] = codedir

        if not os.path.exists(self.config_file_path):
            self.config = self.config_default_get(config=config)
        else:
            self._config_load()

        # merge interactive flags
        if "INTERACTIVE" in self.config:
            self.interactive = interactive and self.config["INTERACTIVE"]
            # enforce interactive flag consistency after having read the config file,
            # arguments overrides config file behaviour
        self.config["INTERACTIVE"] = self.interactive

        if not "DIR_TEMP" in self.config:
            config.update(self.config)
            self.config = self.config_default_get(config=config)

        if readonly:
            self.config["READONLY"] = readonly

        if sshagent_use:
            self.config["SSH_AGENT"] = sshagent_use
        if sshkey:
            self.config["SSH_KEY_DEFAULT"] = sshkey
        if debug_configure:
            self.config["DEBUG"] = debug_configure

        for key, val in config.items():
            self.config[key] = val

        if not sshagent_use and self.interactive:  # just a warning when interactive
            T = """
            Did not find an ssh agent, is this ok?
            It's recommended to have a SSH key as used on github loaded in your ssh-agent
            If the SSH key is not found, repositories will be cloned using https.
            Is better to stop now and to load an ssh-agent with 1 key.
            """
            print(Tools.text_strip(T))
            if self.interactive:
                if not Tools.ask_yes_no("OK to continue?"):
                    sys.exit(1)

        # defaults are now set, lets now configure the system
        if sshagent_use:
            # TODO: this is an error SSH_agent does not work because cannot identify which private key to use
            # see also: https://github.com/threefoldtech/jumpscaleX_core/issues/561
            self.sshagent = SSHAgent()
            self.sshagent.key_default_name
        if secret is None:
            if "SECRET" not in self.config or not self.config["SECRET"]:
                self.secret_set()  # will create a new one only when it doesn't exist
        else:
            self.secret_set(secret)

        if DockerFactory.indocker():
            self.config["IN_DOCKER"] = True
        else:
            self.config["IN_DOCKER"] = False

        self.config_save()
        self.init(configdir=configdir)

    def secret_set(self, secret=None):
        if self.interactive:
            while not secret:  # keep asking till the secret is not empty
                secret = Tools.ask_password("provide secret to use for encrypting private key")
            secret = secret.encode()
        else:
            if not secret:
                secret = str(random.randint(1, 100000000)).encode()
            else:
                secret = secret.encode()

        import hashlib

        m = hashlib.sha256()
        m.update(secret)

        secret2 = m.hexdigest()

        if "SECRET" not in self.config:
            self.config["SECRET"] = ""

        if self.config["SECRET"] != secret2:

            self.config["SECRET"] = secret2

            self.config_save()

    def test(self):
        if not MyEnv.loghandlers != []:
            j.shell()

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
            sys.exit(1)

        exception_obj._logdict = logdict

        if self.debug and tb and pudb:
            # exception_type, exception_obj, tb = sys.exc_info()
            pudb.post_mortem(tb)

        if die == False:
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
    def install(configdir=None, force=False, sandboxed=False):

        MyEnv.init(configdir=configdir)

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
                UbuntuInstaller.base()
        elif "darwin" in MyEnv.platform():
            if not sandboxed:
                OSXInstaller.do_all()
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
        ji.repos_get(pull=False)
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
            Tools.execute(script, interactive=MyEnv.interactive, die_if_args_left=True)

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
            set -ex
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
                "blosc>=1.5.1",
                "Brotli>=0.6.0",
                "captcha",
                "certifi",
                "Cython",
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
                "fakeredis",
                "future>=0.15.0",
                "geopy",
                "geocoder",
                "gevent >= 1.2.2",
                "gipc",
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
                "prompt-toolkit>=2.0.9",
                "pygments-markdown-lexer",
                "wsgidav",
                "bottle==0.12.17",  # why this version?
            ],
            # level 1: in the middle
            1: [
                "zerotier>=1.1.2",
                "python-jose>=2.0.1",
                "itsdangerous>=0.24",
                "jsonschema>=2.5.1",
                "graphene>=2.0",
                "gevent-websocket",
                "ovh>=0.4.7",
                "packet-python>=1.37",
                "uvloop>=0.8.0",
                "pycountry",
                "pycountry_convert",
                "cson>=0.7",
                "ujson",
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
            ],
        }

        res = []

        for piplevel in pips:
            if piplevel <= level:
                res += pips[piplevel]

        return res

    @staticmethod
    def pips_install(items=None):
        if not items:
            items = BaseInstaller.pips_list(3)
        for pip in items:
            if not MyEnv.state_get("pip_%s" % pip):
                C = "pip3 install '%s'" % pip  # --user
                Tools.execute(C, die=True, retry=3)
                MyEnv.state_set("pip_%s" % pip)
        C = "pip3 install -e 'git+https://github.com/threefoldtech/0-hub#egg=zerohub&subdirectory=client'"
        Tools.execute(C, die=True)
        MyEnv.state_set("pip_zoos")

    @staticmethod
    def cleanup_script_get():
        # ncdu is a nice tool to find disk usage
        CMD = """
        cd /
        rm -f /root/.ssh/authorized_keys
        rm -f /tmp/cleanedup
        rm -f /root/.jsx_history
        rm -f /root/.ssh/*
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
        rm -rf /var/backups
        apt-get clean -y
        apt-get autoremove --purge -y
        rm -rf {DIR_BASE}/openresty/pod
        rm -rf {DIR_BASE}/openresty/site
        touch /tmp/cleanedup
        rm -rf /var/lib/apt/lists
        rm -rf /usr/src
        mkdir -p /var/lib/apt/lists
        find . | grep -E "(__pycache__|\.bak$|\.pyc$|\.pyo$|\.rustup|\.cargo)" | xargs rm -rf
        sed -i -r 's/^SECRET =.*/SECRET =/' {DIR_BASE}/cfg/jumpscale_config.toml
        rm -f {DIR_BASE}/cfg/keys/default/*
        """
        return Tools.text_strip(CMD, replace=False)

    @staticmethod
    def cleanup_script_developmentenv_get():
        CMD = """
        apt remove gcc -y
        apt remove rustc -y
        apt remove llvm -y
        rm -rf /usr/lib/x86_64-linux-gnu/libLLVM-6.0.so.1
        rm -rf /usr/lib/llvm-6.0
        rm -rf /usr/lib/gcc
        export SUDO_FORCE_REMOVE=no
        apt-mark manual wireguard-tools
        apt-mark manual sudo
        apt-get autoremove --purge -y
        rm -rf /var/lib/apt/lists
        mkdir -p /var/lib/apt/lists
        """
        return Tools.text_strip(CMD, replace=False)


class OSXInstaller:
    @staticmethod
    def do_all():
        MyEnv._init()
        Tools.log("installing OSX version")
        OSXInstaller.base()
        BaseInstaller.pips_install()

    @staticmethod
    def base():
        MyEnv._init()
        OSXInstaller.brew_install()
        if not Tools.cmd_installed("curl") or not Tools.cmd_installed("unzip") or not Tools.cmd_installed("rsync"):
            script = """
            brew install curl unzip rsync
            """
            Tools.execute(script, replace=True)
        BaseInstaller.pips_install(["click"])  # TODO: *1

    @staticmethod
    def brew_install():
        if not Tools.cmd_installed("brew"):
            cmd = 'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
            Tools.execute(cmd, interactive=True)

    @staticmethod
    def brew_uninstall():
        MyEnv._init()
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
    def do_all(prebuilt=False):
        MyEnv._init()
        Tools.log("installing Ubuntu version")

        UbuntuInstaller.ensure_version()
        UbuntuInstaller.base()
        # UbuntuInstaller.ubuntu_base_install()
        if not prebuilt:
            UbuntuInstaller.python_dev_install()
        UbuntuInstaller.apts_install()
        if not prebuilt:
            BaseInstaller.pips_install()

    @staticmethod
    def ensure_version():
        MyEnv._init()
        if not os.path.exists("/etc/lsb-release"):
            raise Tools.exceptions.Base("Your operating system is not supported")

        return True

    @staticmethod
    def base():
        MyEnv._init()

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
            Tools.execute(script, interactive=True)

        script = """
        apt-get update
        apt-get install -y mc wget python3 git tmux
        set +ex
        apt-get install python3-distutils -y
        set -ex
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
        #apt-get install -y python3.6-dev


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
        ]  # "graphviz"

    @staticmethod
    def apts_install():
        for apt in UbuntuInstaller.apts_list():
            if not MyEnv.state_get("apt_%s" % apt):
                command = "apt-get install -y %s" % apt
                Tools.execute(command, die=True)
                MyEnv.state_set("apt_%s" % apt)

    # def pip3(self):
    #     script="""
    #
    #     cd /tmp
    #     curl -sk https://bootstrap.pypa.io/get-pip.py > /tmp/get-pip.py || die "could not download pip" || return 1
    #     python3 /tmp/get-pip.py  >> ${LogFile} 2>&1 || die "pip install" || return 1
    #     rm -f /tmp/get-pip.py
    #     """
    #     Tools.execute(script,interactive=True)


class JumpscaleInstaller:
    def install(self, sandboxed=False, force=False, gitpull=False, prebuilt=False):

        MyEnv.check_platform()
        # will check if there's already a key loaded (forwarded) will continue installation with it
        rc, _, _ = Tools.execute("ssh-add -L")
        if not rc:
            if "SSH_Agent" in MyEnv.config and MyEnv.config["SSH_Agent"]:
                MyEnv.sshagent.key_default_name  # means we will load ssh-agent and help user to load it properly

        BaseInstaller.install(sandboxed=sandboxed, force=force)

        Tools.file_touch(os.path.join(MyEnv.config["DIR_BASE"], "lib/jumpscale/__init__.py"))

        self.repos_get(pull=gitpull)
        self.repos_link()
        self.cmds_link()

        script = """
        set -e
        cd {DIR_BASE}
        source env.sh
        mkdir -p {DIR_BASE}/openresty/nginx/logs
        mkdir -p {DIR_BASE}/var/log
        kosmos 'j.data.nacl.configure(generate=True,interactive=False)'
        kosmos 'j.core.installer_jumpscale.remove_old_parts()'
        # kosmos --instruct=/tmp/instructions.toml
        kosmos 'j.core.tools.pprint("JumpscaleX init step for nacl (encryption) OK.")'
        """
        Tools.execute(script, die_if_args_left=True)

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
                            except:
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

    def prebuilt_copy(self):
        """
        copy the prebuilt files to the {DIR_BASE} location
        :return:
        """
        self.cmds_link(generate_js=False)
        # why don't we use our primitives here?
        Tools.execute("cp -a {DIR_CODE}/github/threefoldtech/sandbox_threebot_linux64/* /")
        # -a won't copy hidden files
        Tools.execute("cp {DIR_CODE}/github/threefoldtech/sandbox_threebot_linux64/.startup.toml /")
        Tools.execute("source {DIR_BASE}/env.sh; kosmos 'j.data.nacl.configure(generate=True,interactive=False)'")

    def repos_get(self, pull=False, prebuilt=False):
        if prebuilt:
            GITREPOS["prebuilt"] = PREBUILT_REPO

        for NAME, d in GITREPOS.items():
            GITURL, BRANCH, RPATH, DEST = d
            dest = Tools.code_github_get(url=GITURL, rpath=RPATH, branch=BRANCH, pull=pull)
            try:
                dest = Tools.code_github_get(url=GITURL, branch=BRANCH, pull=pull)
            except Exception:
                activate_http = Tools.ask_yes_no(
                    "\n### SSH cloning Failed, your key isn't on github or you're missing permission, Do you want to clone via http?\n"
                )
                if activate_http:
                    MyEnv.interactive = False
                    r = Tools.code_git_rewrite_url(url=URL, ssh=False)
                    # TODO: *1
                    Tools.shell()
                    w
                    Tools.code_github_get(url=GITURL, rpath=RPATH, branch=BRANCH, pull=pull, dest=DEST)
                else:
                    raise Tools.exceptions.Base("\n### Please authenticate your key and try again\n")

        if prebuilt:
            self.prebuilt_copy()

    def repos_link(self):
        """
        link the jumpscale repo's to right location in sandbox
        :return:
        """

        for NAME, d in GITREPOS.items():
            GITURL, BRANCH, PATH, DEST = d

            script = """
            set -e
            rm -f {DEST}
            mkdir -p {DESTPARENT}
            ln -s {GITPATH}/{PATH} {DEST}
            """
            (host, type, account, repo, url2, branch2, GITPATH, RPATH, port) = Tools.code_giturl_parse(url=GITURL)
            srcpath = "%s/%s" % (GITPATH, PATH)
            if not Tools.exists(srcpath):
                raise Tools.exceptions.Base("did not find:%s" % srcpath)

            DESTPARENT = os.path.dirname(DEST.rstrip())

            script = Tools.text_replace(script, args=locals())
            script = Tools.text_replace(script, args=locals())  # NEED TO DO THIS 2x
            if "{" in script:
                from pudb import set_trace

                set_trace()
                script = Tools.text_replace(script, args=locals())
                Tools.shell()
                raise Tools.exceptions.BUG("replace did not work")
            Tools.log(Tools.text_replace("link {GITPATH}/{PATH} {DEST}", args=locals()), data=script)
            Tools.execute(script, args=locals(), die_if_args_left=True)

    def cmds_link(self, generate_js=True):
        _, _, _, _, loc = Tools._code_location_get(repo="jumpscaleX_core/", account="threefoldtech")
        for src in os.listdir("%s/cmds" % loc):
            src2 = os.path.join(loc, "cmds", src)
            dest = "%s/bin/%s" % (MyEnv.config["DIR_BASE"], src)
            if not os.path.exists(dest):
                Tools.link(src2, dest, chmod=770)
        Tools.link("%s/install/jsx.py" % loc, "{DIR_BASE}/bin/jsx", chmod=770)
        if generate_js:
            Tools.execute("cd {DIR_BASE};source env.sh;js_init generate", interactive=False, die_if_args_left=True)


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
    def init(name=None):
        if not DockerFactory._init:
            rc, out, _ = Tools.execute("cat /proc/1/cgroup", die=False, showout=False)
            if rc == 0 and out.find("/docker/") != -1:
                # nothing to do we are in docker already
                return

            MyEnv._init()

            if MyEnv.platform() == "linux" and not Tools.cmd_installed("docker"):
                UbuntuInstaller.docker_install()
                MyEnv._cmd_installed["docker"] = shutil.which("docker")

            if not Tools.cmd_installed("docker"):
                raise Tools.exceptions.Operations("Could not find Docker installed")

            DockerFactory._init = True
            cdir = Tools.text_replace("{DIR_BASE}/var/containers")
            Tools.dir_ensure(cdir)
            for name_found in os.listdir(cdir):
                # to make sure there is no recursive behaviour if called from a docker container
                if name_found != name and name_found.strip().lower() not in ["shared"]:
                    DockerContainer(name_found)

    @staticmethod
    def container_get(name, image="threefoldtech/3bot", start=False, delete=False, ports=None):
        DockerFactory.init()
        if name in DockerFactory._dockers:
            docker = DockerFactory._dockers[name]
            if delete:
                docker.delete()
                # needed because docker object is being retained
                docker.config.save()
        else:
            docker = DockerContainer(name=name, image=image, delete=delete, ports=ports)
        if start:
            docker.start()
        return docker

    @staticmethod
    def containers_running():
        names = Tools.execute("docker ps --format='{{json .Names}}'", showout=False, replace=False)[1].split("\n")
        names = [i.strip("\"'") for i in names if i.strip() != ""]
        return names

    @staticmethod
    def containers_names():
        names = Tools.execute("docker container ls -a --format='{{json .Names}}'", showout=False, replace=False)[
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
        for d in DockerFactory.containers():
            print(" - %-10s : %-15s : %-25s (sshport:%s)" % (d.name, d.config.ipaddr, d.config.image, d.config.sshport))

    @staticmethod
    def container_name_exists(name):
        return name in DockerFactory.containers_names()

    @staticmethod
    def image_names():
        names = Tools.execute("docker images --format='{{.Repository}}:{{.Tag}}'", showout=False, replace=False)[
            1
        ].split("\n")
        names = [i.strip("\"'") for i in names if i.strip() != ""]
        return names

    @staticmethod
    def image_name_exists(name):
        if ":" in name:
            name = name.split(":")[0]
        for name_find in DockerFactory.image_names():
            if name_find.find(name) == 0:
                return name_find
        return False

    @staticmethod
    def image_remove(name):

        for name_find in DockerFactory.image_names():
            if name_find.find(name) != -1:
                Tools.log("remove container:%s" % name_find)
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
        names = Tools.execute("docker images --format='{{.ID}}'", showout=False, replace=False)[1].split("\n")
        for image_id in names:
            if image_id:
                Tools.execute("docker rmi -f %s" % image_id)


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
        self.path_config = "%s/docker_config.toml" % (self.path_vardir)
        # self.wireguard_pubkey
        self.ipaddr = ""

        if delete:
            Tools.delete(self.path_vardir)

        if not Tools.exists(self.path_config):

            self.portrange = None

            if image:
                self.image = image
            else:
                self.image = "threefoldtech/3bot"

            if startupcmd:
                self.startupcmd = startupcmd
            else:
                self.startupcmd = "/sbin/my_init"

        else:
            self.load()

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
        self.load()

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
        self.sshport = ssh
        self.portrange_txt = "-p %s-%s:8005-8009" % (a, b)
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
    def __init__(self, name="default", delete=False, image=None, startupcmd=None, ports=None):
        """
        if you want to start from scratch use: "phusion/baseimage:master"

        if codedir not specified will use {DIR_BASE}/code if exists otherwise ~/code
        """
        if name == "shared":
            raise Tools.exceptions.JSBUG("should never be the shared obj")
        if not DockerFactory._init:
            raise Tools.exceptions.JSBUG("make sure to call DockerFactory.init() bedore getting a container")

        DockerFactory._dockers[name] = self

        self.config = DockerConfig(name=name, image=image, startupcmd=startupcmd, delete=delete, ports=ports)

        if self.config.portrange == None:
            self.config._find_port_range()
            self.config.save()

        if delete:
            self.delete()

            self.config.save()

        if "SSH_Agent" in MyEnv.config and MyEnv.config["SSH_Agent"]:
            MyEnv.sshagent.key_default_name  # means we will load ssh-agent and help user to load it properly

        if len(MyEnv.sshagent.keys_list()) == 0:
            raise Tools.exceptions.Base("Please load your ssh-agent with a key!")

        self._wireguard = None

    @property
    def container_exists_config(self):
        """
        returns True if the container is defined on the filesystem with the config file
        :return:
        """
        if Tools.exists(self._path):
            return True

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
        if self.config.image != val:
            self.config.image = val
            self.config.save()

    @property
    def name(self):
        return self.config.name

    def start(self, mount_dirs=True, stop=False):
        if not self.container_exists_config:
            raise Tools.exceptions.Operations("ERROR: cannot find docker with name:%s, cannot start" % self.name)
        if self.container_exists_in_docker:
            if not self.isrunning():
                Tools.execute("docker start %s" % self.name, showout=False)
            return
        self.install(mount_dirs=mount_dirs, stop=stop)

    def install(self, mount_dirs=True, update=None, portmap=True, stop=False, delete=False):
        """

        :param update: is yes will upgrade the ubuntu
        :param mount_dirs if mounts will be done from host system
        :return:
        """

        args = {}
        args["NAME"] = self.config.name
        # is to make sure we have the right name for the image
        image2 = DockerFactory.image_name_exists(self.config.image)
        if not image2:
            image2 = self.config.image
        args["IMAGE"] = image2

        if ":" in image2:
            image2 = image2.split(":")[0]

        if delete:
            self.delete()

        if stop:
            self.stop()

        if not self.container_exists_config:
            # means is a new one
            new = True
            if update == None:
                if image2 in ["threefoldtech/base", "threefoldtech/3bot", "threefoldtech/3botdev"]:
                    update = False
            if not update:
                try:
                    self.dexec("cat /root/.BASEINSTALL_OK")
                    update = False
                except:
                    pass
        else:
            # new means docker container was never created (configured)
            new = False

        # UPDATE THE CONFIG IN THE DOCKER CFG DIRECTORY (ALWAYS USE THE HOST AS BASIS)
        Tools.dir_ensure(self._path + "/cfg")
        Tools.dir_ensure(self._path + "/var")
        CONFIG = {}
        for i in [
            "USEGIT",
            "DEBUG",
            "LOGGER_INCLUDE",
            "LOGGER_EXCLUDE",
            "LOGGER_LEVEL",
            "LOGGER_CONSOLE",
            "LOGGER_REDIS",
            "SECRET",
        ]:
            if i in MyEnv.config:
                CONFIG[i] = MyEnv.config[i]

        Tools.config_save(self._path + "/cfg/jumpscale_config.toml", CONFIG)

        if self.container_exists_in_docker and not self.isrunning():
            if not delete:
                Tools.execute("docker start %s" % self.name, showout=False)
            else:
                raise Tools.exceptions.JSBUG("should not get here")
            new = False

        if new or delete or not self.container_running:
            # lets make sure we have the latest image
            run_image_update_cmd = Tools.text_replace("docker image pull {IMAGE}", args=args)
            Tools.execute(run_image_update_cmd, interactive=False)

            # Now create the container
            MOUNTS = ""
            if mount_dirs:
                MOUNTS = """
                -v {DIR_CODE}:/sandbox/code \
                -v {DIR_BASE}/var/containers/shared:/sandbox/myhost \
                """
                # -v {DIR_BASE}/var/containers/{NAME}/var:/sandbox/var \
                # -v {DIR_BASE}/var/containers/{NAME}/cfg:/sandbox/cfg \

            args["MOUNTS"] = Tools.text_replace(MOUNTS.strip(), args=args)
            args["CMD"] = self.config.startupcmd
            if portmap:
                args["PORTRANGE"] = self.config.ports_txt
            else:
                args["PORTRANGE"] = ""
            run_cmd = (
                "docker run --name={NAME} --hostname={NAME} -d {PORTRANGE} \
            --device=/dev/net/tun --cap-add=NET_ADMIN --cap-add=SYS_ADMIN --cap-add=DAC_OVERRIDE \
            --cap-add=DAC_READ_SEARCH {MOUNTS} {IMAGE} {CMD}".strip()
            )
            run_cmd2 = Tools.text_replace(re.sub("\s+", " ", run_cmd), args=args)

            print(" - Docker machine gets created: ")
            print(run_cmd2)
            Tools.execute(run_cmd2, interactive=False)
            new = True

        if update:
            self.dexec("rm -f /root/.BASEINSTALL_OK")
            print(" - Upgrade ubuntu")
            self.dexec("add-apt-repository ppa:wireguard/wireguard -y")
            self.dexec("apt-get update")
            self.dexec("DEBIAN_FRONTEND=noninteractive apt-get -y upgrade --force-yes")
            print(" - Upgrade ubuntu ended")
            self.dexec("apt-get install mc git -y")
            self.dexec("apt-get install python3 -y")
            self.dexec("apt-get install wget tmux -y")
            self.dexec("apt-get install curl rsync unzip redis-server -y")
            self.dexec("apt-get install python3-distutils python3-psutil python3-pip python3-click -y")
            self.dexec("locale-gen --purge en_US.UTF-8")
            self.dexec("apt-get install software-properties-common -y")
            self.dexec("apt-get install wireguard -y")
            self.dexec("apt-get install locales -y")
            self.dexec("touch /root/.BASEINSTALL_OK")

        if update or new:
            print(" - Configure / Start SSH server")
            self.dexec("rm -rf /sandbox/cfg/keys")
            self.dexec("rm -f /root/.ssh/authorized_keys;/etc/init.d/ssh stop 2>&1 > /dev/null", die=False)
            self.dexec("/usr/bin/ssh-keygen -A")
            self.dexec("/etc/init.d/ssh start")
            self.dexec("rm -f /etc/service/sshd/down")

            # get our own loaded ssh pub keys into the container
            SSHKEYS = Tools.execute("ssh-add -L", die=False, showout=False)[1]
            if SSHKEYS.strip() != "":
                self.dexec('echo "%s" > /root/.ssh/authorized_keys' % SSHKEYS)
            Tools.execute("mkdir -p {0}/.ssh && touch {0}/.ssh/known_hosts".format(MyEnv.config["DIR_HOME"]))
            Tools.execute(
                'ssh-keygen -f "%s/.ssh/known_hosts" -R "[localhost]:%s"'
                % (MyEnv.config["DIR_HOME"], self.config.sshport)
            )

        print(" - Create route to main 3bot container")

        cmd = "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' %s" % self.name
        rc, out, err = Tools.execute(cmd, replace=False, showout=False, die=False)
        if rc == 0:
            self.config.ipaddr = out.strip()
            self.config.save()

        if DockerFactory.container_name_exists("3bot") and self.name != "3bot":
            d = DockerFactory.container_get("3bot")
            cmd = "ip route add 10.10.0.0/16 via %s" % d.config.ipaddr

        print(" - CONTAINER STARTED")

    def dexec(self, cmd, interactive=False, die=True):
        if "'" in cmd:
            cmd = cmd.replace("'", '"')
        if interactive:
            cmd2 = "docker exec -ti %s bash -c '%s'" % (self.name, cmd)
        else:
            cmd2 = "docker exec -t %s bash -c '%s'" % (self.name, cmd)
        Tools.execute(cmd2, interactive=interactive, showout=True, replace=False, asfile=True, die=die)

    def sshshell(self):
        if not self.isrunning():
            self.start()
        sshport = str(self.config.sshport)
        home = MyEnv.config["DIR_HOME"]
        Tools.execute('ssh-keygen -f "%s/.ssh/known_hosts" -R "[localhost]:%s"' % (home, sshport))
        os.execv(
            shutil.which("ssh"), ["ssh", "root@localhost", "-A", "-t", "-oStrictHostKeyChecking=no", "-p", sshport]
        )

    def shell(self):
        if not self.isrunning():
            self.start()
        self.dexec("mc", interactive=True)

    def diskusage(self):
        """
        uses ncdu to visualize disk usage
        :return:
        """
        self.dexec("apt update;apt install ncdu -y;ncdu", interactive=True)

    def sshexec(self, cmd, retry=None, asfile=True):
        if "'" in cmd:
            cmd = cmd.replace("'", '"')
        cmd2 = "ssh -oStrictHostKeyChecking=no -t root@localhost -A -p %s '%s'" % (self.config.sshport, cmd)
        Tools.execute(
            cmd2, interactive=True, showout=False, replace=False, asfile=asfile, timeout=3600 * 2, retry=retry
        )

    def jsxexec(self, cmd, **kwargs):
        """
        execute a jumpscale command in container, can be multiline
        :param cmd:
        :return:
        """
        if callable(cmd):
            method_name, cmd = Tools.method_code_get(cmd, **kwargs)
            cmd += "%s()" % method_name
        name = self.config.name
        sshport = self.config.sshport
        cmd = "from Jumpscale import j\n%s" % cmd
        Tools.file_write(f"/tmp/{name}.py", cmd)
        cmd = f"scp -P {sshport} /tmp/{name}.py root@localhost:/tmp/{name}.py"
        Tools.execute(cmd, showout=False, replace=False)
        cmd = f"source /sandbox/env.sh;kosmos -p /tmp/{name}.py"
        self.sshexec(cmd, asfile=True)

    def kosmos(self):
        self.jsxexec("j.shell()")

    def stop(self):
        if self.container_running:
            Tools.execute("docker stop %s" % self.name, showout=False)
        if self.container_exists_in_docker:
            Tools.execute("docker rm -f %s" % self.name, die=False, showout=False)

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
        self.config.done_reset()

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
            except:
                Tools.delete("%s/%s" % (dpath, item))
            if version > highest:
                highest = version
        return highest

    def import_(self, path=None, name=None, version=None, imagename=None, start=True, mount_dirs=True, portmap=True):
        """

        :param path:  if not specified will be {DIR_BASE}/var/containers/$name/exports/$version.tar
        :param version: version of the export, if not specified & path not specified will be last in the path
        :param imagename: docker image name as used by docker to import to
        :param start: start the container after import
        :param mount_dirs: do you want to mount the dirs to host
        :param portmap: do you want to do the portmappings (ssh is always mapped)
        :return:
        """
        if not imagename:
            imagename = self.image

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
        DockerFactory.image_remove(imagename)

        print("import docker:%s to %s, will take a while" % (path, self.name))
        Tools.execute("docker import %s %s" % (path, imagename))
        if start:
            self.config.image = imagename
            self.config.save()
            self.delete()
            self.install(update=False, mount_dirs=mount_dirs)
            self.start()

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

    def save(self, clean_runtime=False, clean_devel=False, image=None):
        """

        :param clean_runtime: remove all files not needed for a runtime environment
        :param clean_devel: remove all files not needed for a development environment and a runtime environment
        :param image:
        :return:
        """
        if image:
            self.image = image

        def save_internal():
            image = self.image
            if ":" in image:
                image = image.split(":")[0]
            cmd = "docker rmi -f %s" % image
            Tools.execute(cmd, die=False)
            cmd = "docker rmi -f %s:latest" % image
            Tools.execute(cmd, die=False)
            cmd = "docker commit -p %s %s" % (self.name, image)
            print(" - %s" % cmd)
            Tools.execute(cmd)

        save_internal()

        def clean(container, CLEANUPCMD):
            for line in CLEANUPCMD.split("\n"):
                line = line.strip()
                print(" - cleanup:%s" % line)
                container.dexec(line, die=False)

        if clean_runtime or clean_devel:
            self.stop()
            self.start(mount_dirs=False)
            clean(self, BaseInstaller.cleanup_script_get())
            ##LETS FOR NOW NOT DO IT YET, THERE SEEM TO BE SOME ISSUES
            ##TODO: needs to be fixed to allow the base 3bot image to be smaller
            # if clean_devel:
            #     clean(self, BaseInstaller.cleanup_script_developmentenv_get())
            ename = image.replace("/", "_")
            if ":" in ename:
                ename = ename.split(":")[0]
            self.export(name=ename)
            self.import_(name=ename, start=True)  # will start as well

        if ":" in image:
            image = image.split(":")[0]
        self.image = image

        self.config.save()

    def push(self, image=None):
        if not image:
            image = self.image
        cmd = "docker push %s" % image
        Tools.execute(cmd)

    def jumpscale_install(
        self, secret=None, privatekey=None, redo=False, threebot=True, pull=False, branch=None, prebuilt=False
    ):

        args_txt = ""
        if secret:
            args_txt += " --secret='%s'" % secret
        if privatekey:
            args_txt += " --privatekey='%s'" % privatekey
        if redo:
            args_txt += " -r"
        if threebot:
            args_txt += " --threebot"
        if pull:
            args_txt += " --pull"
        if branch:
            args_txt += " --branch %s" % branch
        if not MyEnv.interactive:
            args_txt += " --no-interactive"
        if prebuilt:
            args_txt += " --prebuilt"

        dirpath = os.path.dirname(inspect.getfile(Tools))
        if dirpath.startswith(MyEnv.config["DIR_CODE"]):
            cmd = (
                "python3 /sandbox/code/github/threefoldtech/jumpscaleX_core/install/jsx.py configure --sshkey %s -s"
                % MyEnv.sshagent.key_default_name
            )
            Tools.log("CONFIGURE THE CONTAINER", data=cmd)
            self.sshexec(cmd)
            self.sshexec("rm -f /tmp/InstallTools.py;rm -f /tmp/jsx")
            cmd = "python3 /sandbox/code/github/threefoldtech/jumpscaleX_core/install/jsx.py install -s"
            cmd += args_txt
        else:
            print(" - copy installer over from where I install from")
            dirpath2 = "/sandbox/code/github/threefoldtech/jumpscaleX_core/install/"
            if not Tools.exists(dirpath2):
                dirpath2 = dirpath
            for item in ["jsx", "InstallTools.py"]:
                src1 = "%s/%s" % (dirpath2, item)
                cmd = "scp -P {} -o StrictHostKeyChecking=no \
                    -o UserKnownHostsFile=/dev/null \
                    -r {} root@localhost:/tmp/".format(
                    self.config.sshport, src1
                )
                Tools.execute(cmd)

                cmd = (
                    "cd /tmp;python3 jsx configure --sshkey %s -s;python3 jsx install -s"
                    % MyEnv.sshagent.key_default_name
                )
                cmd += args_txt
        print(" - Installing jumpscaleX ")
        self.sshexec("apt-get install python3-click -y")
        self.sshexec(cmd, retry=2)

        cmd = """
        echo 'autoclean'
        apt-get autoclean -y
        apt-get clean -y
        apt-get autoremove -y
        """
        self.sshexec(cmd)

        k = """

        install succesfull:

        # if you use a container do:
        /tmp/jsx container-kosmos

        or

        kosmos

        """
        args = {}
        args["port"] = self.config.sshport
        print(Tools.text_replace(k, args=args))

    def __repr__(self):
        return "# CONTAINER: \n %s" % Tools._data_serializer_safe(self.config.__dict__)

    __str__ = __repr__

    @property
    def wireguard(self):
        if not self._wireguard:
            self._wireguard = WireGuardServer(addr="127.0.0.1", port=self.config.sshport)
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

    def _key_name_get(self, name):
        if not name:
            if MyEnv.config["SSH_KEY_DEFAULT"]:
                name = MyEnv.config["SSH_KEY_DEFAULT"]
            elif MyEnv.interactive:
                name = Tools.ask_string("give name for your sshkey")
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
        name = self._key_name_get(name)

        if not passphrase:
            if MyEnv.config["interactive"]:
                passphrase = Tools.ask_password(
                    "passphrase for ssh key to generate, \
                        press enter to skip and not use a passphrase"
                )

        path = Tools.text_replace("{DIR_HOME}/.ssh/%s" % name)
        Tools.Ensure("{DIR_HOME}/.ssh")

        if reset:
            Tools.delete("%s" % path)
            Tools.delete("%s.pub" % path)

        if not Tools.exists(path) or reset:
            if passphrase:
                cmd = 'ssh-keygen -t rsa -f {} -N "{}"'.format(path, passphrase)
            else:
                cmd = "ssh-keygen -t rsa -f {}".format(path)
            Tools.execute(cmd, timeout=10)

            Tools.log("load generated sshkey: %s" % path)

    @property
    def key_default_name(self):
        """

        kosmos 'print(MyEnv.sshagent.key_default)'

        checks if it can find the default key for ssh-agent, if not will ask
        :return:
        """

        def ask_key(key_names):
            if len(key_names) == 1:
                # if MyEnv.interactive:
                #     if not Tools.ask_yes_no("Ok to use key: '%s' as your default key?" % key_names[0]):
                #         return None
                name = key_names[0]
            elif len(key_names) == 0:
                raise Tools.exceptions.Operations(
                    "Cannot find a possible ssh-key, please load your possible keys in your ssh-agent or have in your homedir/.ssh"
                )
            else:
                if MyEnv.interactive:
                    name = Tools.ask_choices("Which is your default sshkey to use", key_names)
                else:
                    name = "id_rsa"
            return name

        self._keys  # will fetch the keys if not possible will show error

        sshkey = MyEnv.config["SSH_KEY_DEFAULT"]

        if not sshkey:
            if len(self.key_names) > 0:
                sshkey = ask_key(self.key_names)
        if not sshkey:
            hdir = Tools.text_replace("{DIR_HOME}/.ssh")
            if not Tools.exists(hdir):
                msg = "cannot find home dir:%s" % hdir
                msg += "\n### Please get a ssh key or generate one using ssh-keygen\n"
                raise Tools.exceptions.Operations(msg)
            choices = []
            for item in os.listdir(hdir):
                item2 = item.lower()
                if not (
                    item.startswith(".")
                    or item2.endswith((".pub", ".backup", ".toml", ".old"))
                    or item in ["known_hosts", "config", "authorized_keys"]
                ):
                    choices.append(item)
            sshkey = ask_key(choices)

        if not sshkey in self.key_names:
            if DockerFactory.indocker():
                raise Tools.exceptions.Base("sshkey should be passed forward by means of SSHAgent")
            self.key_load(name=sshkey)
            assert sshkey in self.key_names

        if MyEnv.config["SSH_KEY_DEFAULT"] != sshkey:
            MyEnv.config["SSH_KEY_DEFAULT"] = sshkey
            MyEnv.config_save()

        return sshkey

    def key_load(self, path=None, name=None, passphrase=None, duration=3600 * 24):
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

        if name:
            path = Tools.text_replace("{DIR_HOME}/.ssh/%s" % name)
        elif path:
            name = os.path.basename(path)
        else:
            name = self._key_name_get(name)
            path = Tools.text_replace("{DIR_HOME}/.ssh/%s" % name)

        if name in self.key_names:
            return

        if not Tools.exists(path):
            raise Tools.exceptions.Base("Cannot find path:%sfor sshkey (private key)" % path)

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
            rc, out, err = Tools.execute(C, showout=True, die=False)
            if rc > 0:
                Tools.delete("/tmp/ap-cat.sh")
                raise Tools.exceptions.Operations("Could not load sshkey with passphrase (%s)" % path)
        else:
            # load without passphrase
            cmd = "ssh-add -t %s %s " % (duration, path)
            rc, out, err = Tools.execute(cmd, showout=True, die=False)
            if rc > 0:
                raise Tools.exceptions.Operations("Could not load sshkey without passphrase (%s)" % path)

        self.reset()

        return name, path

    @property
    def _keys(self):
        """
        """
        if self.__keys is None:
            self._read_keys()
        return self.__keys

    def _read_keys(self):
        return_code, out, err = Tools.execute("ssh-add -L", showout=False, die=False, timeout=1)
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

    def keypub_path_get(self, keyname="", die=True):
        """
        Returns Path of public key that is loaded in the agent

        :param keyname: name of key loaded to agent to get its path, if empty will check if there is 1 loaded, defaults to ""
        :type keyname: str, optional
        :param die:Raise error if True,else do nothing, defaults to True
        :type die: bool, optional
        :raises RuntimeError: Key not found with given keyname
        :return: path of public key
        :rtype: str
        """
        keyname = j.sal.fs.getBaseName(keyname)
        Tools.shell()
        for item in self.keys_list():
            if item.endswith(keyname):
                return item
        if die:
            raise Tools.exceptions.Base(
                "Did not find key with name:%s, check its loaded in ssh-agent with ssh-add -l" % keyname
            )

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

        Tools.process_kill_by_by_filter("ssh-agent")

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
        Tools.process_kill_by_by_filter("ssh-agent")
        Tools.delete(self.ssh_socket_path)
        # Tools.delete("/tmp", "ssh-agent-pid"))
        self.reset()


class ExecutorSSH:
    def __init__(self, addr=None, port=22, debug=False, checkok=True):
        self.addr = addr
        self.port = port
        self.debug = debug
        self.checkok = checkok
        self._id = None
        self._env = {}
        self.readonly = False
        self.CURDIR = ""
        self._data_path = "/var/executor_data"
        self._init3()

    def reset(self):
        self.state_reset()
        self._init3()
        self.save()

    def _init3(self):
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
        rc, _, _ = self.execute("test -e %s" % path, die=False, showout=False, asfile=False)
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
        if isinstance(content, str) and not "'" in content:

            cmd = 'echo -n -e "%s" > %s' % (content, path)
            self.execute(cmd, asfile=False)
        else:
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
                self.execute(cmd, showout=False, script=False, interactive=False, asfile=False)

        return None

    @property
    def uid(self):
        if self._id is None:
            raise j.exceptions.Base("self._id cannot be None")
        return self._id

    def _commands_transform(self, cmds, die=True, checkok=False, env=None, sudo=False, shell=False):
        # print ("TRANSF:%s"%cmds)

        if sudo or shell:
            checkok = False

        if not env:
            env = {}

        multicommand = "\n" in cmds or ";" in cmds

        if shell:
            if "\n" in cmds:
                raise j.exceptions.Base("cannot do shell for multiline scripts")
            else:
                cmds = "bash -c '%s'" % cmds

        pre = ""

        checkok = checkok or self.checkok

        if die:
            # first make sure not already one
            if "set -e" not in cmds:
                # now only do if multicommands
                if multicommand:
                    if self.debug:
                        pre += "set -ex\n"
                    else:
                        pre += "set -e\n"

        if self.CURDIR != "":
            pre += "cd %s\n" % (self.CURDIR)

        if env != {}:
            for key, val in env.items():
                pre += "export %s=%s\n" % (key, val)

        cmds = "%s\n%s" % (pre, cmds)

        if checkok and multicommand:
            if not cmds.endswith("\n"):
                cmds += "\n"
            cmds += "echo '**OK**'"

        # if "\n" in cmds:
        #     cmds = cmds.replace("\n", ";")
        #     cmds.strip() + "\n"

        # cmds = cmds.replace(";;", ";").strip(";")

        if sudo:
            cmds = self.sudo_cmd(cmds)

        cmds = Tools.text_strip(cmds)

        Tools.log(cmds)

        return cmds

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

        if not "IN_DOCKER" in self.config:
            rc, out, _ = self.execute("cat /proc/1/cgroup", die=False, showout=False, interactive=False)
            if rc == 0 and out.find("/docker/") != -1:
                self.config["IN_DOCKER"] = True
            else:
                self.config["IN_DOCKER"] = False
            self.save()
        return self.config["IN_DOCKER"]

    # @property
    # def env_on_system(self):
    #     if not self._env_on_system:
    #         self.systemenv_load()
    #         self._env_on_system = pickle.loads(self.env_on_system_msgpack)
    #     return self._env_on_system
    #
    # @property
    # def env(self):
    #     return self.env_on_system["ENV"]

    @property
    def state(self):
        if "state" not in self.config:
            self.config["state"] = {}
        return self.config["state"]

    def state_exists(self, key):
        key = j.core.text.strip_to_ascii_dense(key)
        return key in self.state

    def state_set(self, key, val=None, save=True):
        key = j.core.text.strip_to_ascii_dense(key)
        if key not in self.state or self.state[key] != val:
            self.state[key] = val
            self.save()

    def state_get(self, key, default_val=None):
        key = j.core.text.strip_to_ascii_dense(key)
        if key not in self.state:
            if default_val:
                self.state[key] = default_val
                return default_val
            else:
                return None
        else:
            return self.state[key]

    def state_delete(self, key):
        key = j.core.text.strip_to_ascii_dense(key)
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
            rconfig = j.core.tools.config_load(content=res["CFG_JUMPSCALE"])
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
                self.config[name] = res["CFG_JUMPSCALE"]
                return
            if name not in self.config:
                self.config[name] = default

        get_cfg("DIR_HOME", res["ENV"]["HOME"])
        get_cfg("DIR_BASE", "/sandbox")
        get_cfg("DIR_CFG", "%s/cfg" % self.config[name])
        get_cfg("DIR_TEMP", "/tmp")
        get_cfg("DIR_VAR", "%s/var" % self.config[name])
        get_cfg("DIR_CODE", "%s/code" % self.config[name])
        get_cfg("DIR_BIN", "/usr/local/bin")

    def execute(
        self,
        cmd,
        die=True,
        showout=False,
        timeout=1000,
        env=None,
        sudo=False,
        replace=True,
        interactive=False,
        asfile=None,
        retry=None,
        args=None,
    ):
        if replace:
            cmd = self._replace(cmd, args=args)
        if env or args or asfile or sudo:
            cmd = self._commands_transform(cmds=cmd, die=die, checkok=self.checkok, env=env, sudo=sudo, shell=False)
        if asfile == None:
            if asfile or "\n" in cmd or "'" in cmd:
                asfile = True
            else:
                asfile = False
        if asfile:
            self.file_write("/tmp/executor.sh", cmd)
            cmd = "bash /tmp/executor.sh"
        if interactive:
            cmd2 = "ssh -oStrictHostKeyChecking=no -t root@%s -A -p %s '%s'" % (self.addr, self.port, cmd)
        else:
            cmd2 = "ssh -oStrictHostKeyChecking=no root@%s -A -p %s '%s'" % (self.addr, self.port, cmd)
        return Tools.execute(
            cmd2,
            interactive=interactive,
            showout=showout,
            replace=False,
            asfile=False,
            timeout=timeout,
            retry=retry,
            die=die,
        )

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
            Tools.execute(cmd, showout=True, replace=False, asfile=False)
            return
        raise Tools.exceptions.RuntimeError("not implemented")
        dest = self._replace(dest)
        if dest[0] != "/":
            raise j.exceptions.RuntimeError("need / in beginning of dest path")
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

        destdir = os.path.dirname(source)
        Tools.dir_ensure(destdir)

        cmd = "scp -P %s root@%s:%s %s" % (self.port, self.addr, source, dest)
        Tools.execute(cmd, showout=True, replace=False, asfile=False)

    def jsxexec(self, cmd, **kwargs):
        """
        execute a jumpscale command in container, can be multiline
        :param cmd:
        :return:
        """
        if callable(cmd):
            method_name, cmd = Tools.method_code_get(cmd, **kwargs)
            cmd += "%s()" % method_name
        name = "executor"
        sshport = self.sshport
        cmd = "from Jumpscale import j\n%s" % cmd
        # Tools.file_write(f"/tmp/{name}.py", cmd)
        # cmd = f"scp -P {sshport} /tmp/{name}.py root@localhost:/tmp/{name}.py"
        # Tools.execute(cmd, showout=False, replace=False)
        self.file_write(f"/tmp/{name}.py", cmd)
        cmd = f"source /sandbox/env.sh;kosmos -p /tmp/{name}.py"
        self.execute(cmd)

    def kosmos(self):
        self.jsxexec("j.shell()")

    @property
    def uid(self):
        if not "uid" in self.config:
            self.config["uid"] = str(random.getrandbits(32))
            self.save()
        return self.config["uid"]

    def state_reset(self):
        self.config["state"] = {}
        self.save()


class WireGuardServer:
    """
    the server is over SSH, the one running this tool is the client
    and has access to local machine

    myid is unique id < 255*255

    """

    def __init__(self, addr=None, port=22, myid=1):
        self._config = None
        assert addr
        self.addr = addr
        self.port = port
        self.port_wireguard = 9001
        self.myid = 1
        self.serverid = 200

        self._config_local = None
        self.executor = ExecutorSSH(addr, port)

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
        if not self._config_local:
            self._config_local = Tools.config_load("{DIR_BASE}/cfg/wireguard.toml")
            if "WIREGUARD_CLIENT_PRIVKEY" not in self._config_local:
                privkey, pubkey = self.generate_key_pair()
                self._config_local["WIREGUARD_CLIENT_PUBKEY"] = pubkey
                self._config_local["WIREGUARD_CLIENT_PRIVKEY"] = privkey
                Tools.config_save("{DIR_BASE}/cfg/wireguard.toml", self._config_local)
        return self._config_local

    def save(self):
        self.executor.save()
        Tools.config_save("{DIR_BASE}/cfg/wireguard.toml", self.config_local)

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
        path = "{DIR_BASE}/cfg/wireguard/%s/wg0.conf" % self.serverid
        path = Tools.text_replace(path)
        Tools.dir_ensure(os.path.dirname(path))
        Tools.file_write(path, C)
        # print("WIREGUARD CONFIFURATION:\n\n%s" % config)
        # print("WIREGUARD CONFIG PATH:%s" % path)
        if MyEnv.platform() == "linux":
            rc, out, err = Tools.execute("ip link del dev wg0", showout=False, die=False)
            cmd = "/usr/local/bin/bash /usr/local/bin/wg-quick up %s" % path
            Tools.execute(cmd)
            Tools.shell()
        else:
            cmd = "/usr/local/bin/bash /usr/local/bin/wg-quick down %s" % path
            Tools.execute(cmd, die=False)
            cmd = "/usr/local/bin/bash /usr/local/bin/wg-quick up %s" % path
            print(cmd)
            Tools.execute(cmd)
