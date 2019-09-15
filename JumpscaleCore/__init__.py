import os
import socket
import inspect
import sys
from importlib import util

os.environ["LC_ALL"] = "en_US.UTF-8"


def tcpPortConnectionTest(ipaddr, port, timeout=None):
    conn = None
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


def profileStart():
    import cProfile

    pr = cProfile.Profile()
    pr.enable()
    return pr


def profileStop(pr):
    pr.disable()
    import io
    import pstats

    s = io.StringIO()
    sortby = "cumulative"
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


# pr=profileStart()

spec = util.spec_from_file_location("IT", "/%s/core/InstallTools.py" % os.path.dirname(__file__))


from .core.InstallTools import BaseInstaller
from .core.InstallTools import JumpscaleInstaller
from .core.InstallTools import Tools
from .core.InstallTools import RedisTools

from .core.InstallTools import MyEnv
import yaml

MyEnv.init()
# TODO: there is something not right we get different version of this class, this should be like a singleton !!!


class Core:
    def __init__(self, j):
        self._dir_home = None
        self._dir_jumpscale = None
        self._isSandbox = None
        self.db = MyEnv.db

    def db_reset(self, j):
        if hasattr(j.data, "cache"):
            j.data.cache._cache = {}
        self.db = j.clients.redis.core_get(fromcache=False)

    @property
    def dir_jumpscale(self):
        if self._dir_jumpscale is None:
            self._dir_jumpscale = os.path.dirname(os.path.dirname(__file__))
        return self._dir_jumpscale

    @property
    def isSandbox(self):
        if self._isSandbox is None:
            if self.dir_jumpscale.startswith("/sandbox"):
                self._isSandbox = True
            else:
                self._isSandbox = False
        return self._isSandbox

    @staticmethod
    def _data_serializer_safe(data):
        if isinstance(data, dict):
            data = data.copy()  # important to have a shallow copy of data so we don't change original
            for key in ["passwd", "password", "secret"]:
                if key in data:
                    data[key] = "***"
            try:
                serialized = yaml.dump(data, default_flow_style=False, default_style="", indent=4, line_break="\n")
            except Exception as e:
                serialized = "CANNOT SERIALIZE CORE FOR DICT"

        elif isinstance(data, list) or isinstance(data, set):
            try:
                serialized = yaml.dump(data, default_flow_style=False, default_style="", indent=4, line_break="\n")
            except Exception as e:
                serialized = "CANNOT SERIALIZE CORE FOR LIST"
        else:
            try:
                serialized = str(data)
                # to deal with special value
                if serialized == "2147483647":
                    serialized = ""
            except Exception as e:
                serialized = "CANNOT SERIALIZE CORE FOR STR"
        return serialized


from .core.KosmosShell import KosmosShellConfig, ptconfig


class Jumpscale:
    def __init__(self):
        self._shell = None
        self.exceptions = None
        # Tools.j=self

    def _locals_get(self, locals_):
        def add(locals_, name, obj):
            if name not in locals_:
                locals_[name] = obj
            return locals_

        # try:
        #     locals_ = add(locals_, "ssh", j.clients.ssh)
        # except:
        #     pass
        # try:
        #     locals_ = add(locals_, "iyo", j.clients.itsyouonline)
        # except:
        #     pass

        # locals_ = add(locals_,"zos",j.kosmos.zos)

        return locals_

    def shell(self, loc=True, exit=False, locals_=None, globals_=None):

        import inspect

        KosmosShellConfig.j = self
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        f = calframe[1]
        if loc:
            print("\n*** file: %s" % f.filename)
            print("*** function: %s [linenr:%s]\n" % (f.function, f.lineno))
        from ptpython.repl import embed

        # Tools.clear()
        history_filename = "%s/.jsx_history" % MyEnv.config["DIR_HOME"]
        if not Tools.exists(history_filename):
            Tools.file_write(history_filename, "")
        # locals_= f.f_locals
        # if curframe.f_back.f_back is not None:
        #     locals_=curframe.f_back.f_back.f_locals
        # else:
        if not locals_:
            locals_ = curframe.f_back.f_locals
        locals_ = self._locals_get(locals_)
        if not globals_:
            globals_ = curframe.f_back.f_globals
        if exit:
            sys.exit(embed(globals_, locals_, configure=ptconfig, history_filename=history_filename))
        else:
            embed(globals_, locals_, configure=ptconfig, history_filename=history_filename)

    def shelli(self, loc=True, name=None, stack_depth=2):
        if self._shell == None:
            from IPython.terminal.embed import InteractiveShellEmbed

            if name is not "":
                name = "SHELL:%s" % name
            self._shell = InteractiveShellEmbed(banner1=name, exit_msg="")
        if loc:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            f = calframe[1]
            print("\n*** file: %s" % f.filename)
            print("*** function: %s [linenr:%s]\n" % (f.function, f.lineno))
        # self.clear()
        return self._shell(stack_depth=stack_depth)

    def debug(self):
        # disable console logging when entering interactive debugger
        j.core.myenv.log_console = False
        import sys

        if j.core.myenv.debugger == "pudb":
            import pudb
            import threading

            dbg = pudb._get_debugger()

            if isinstance(threading.current_thread(), threading._MainThread):
                pudb.set_interrupt_handler()

            dbg.set_trace(sys._getframe().f_back, paused=True)
        elif j.core.myenv.debugger == "ipdb":
            try:
                import ipdb as debugger
            except ImportError:
                import pdb

                debugger = pdb.Pdb()
            debugger.set_trace(sys._getframe().f_back)


j = Jumpscale()
j.core = Core(j)
j.core._groups = {}


rootdir = os.path.dirname(os.path.abspath(__file__))
# print("- setup root directory: %s" % rootdir)


j.core.myenv = MyEnv
j.core.redistools = RedisTools

j.core.installer_base = BaseInstaller
j.core.installer_jumpscale = JumpscaleInstaller()
j.core.tools = Tools

j.core.tools._data_serializer_safe = j.core._data_serializer_safe

j.core.profileStart = profileStart
j.core.profileStop = profileStop

# pr=profileStart()

from .core.Text import Text

j.core.text = Text(j)

from .core.Dirs import Dirs

j.dirs = Dirs(j)
j.core.dirs = j.dirs

# from .core.logging.LoggerFactory import LoggerFactory
# j.logger = LoggerFactory(j)
# j.core.logger = j.logger


from .core.BASECLASSES.BaseClasses import BaseClasses

j.baseclasses = BaseClasses()


from .core.Application import Application

j.application = Application(j)
j.core.application = j.application


from .core.cache.Cache import Cache

j.core.cache = Cache(j)

from .core.PlatformTypes import PlatformTypes

j.core.platformtype = PlatformTypes(j)

from .core.errorhandler.ErrorHandler import ErrorHandler

j.errorhandler = ErrorHandler(j)
j.core.errorhandler = j.errorhandler
j.exceptions = j.errorhandler.exceptions
j.core.exceptions = j.exceptions


# THIS SHOULD BE THE END OF OUR CORE, EVERYTHING AFTER THIS SHOULD BE LOADED DYNAMICALLY

j.core.application._lib_generation_path = j.core.tools.text_replace("{DIR_BASE}/lib/jumpscale/jumpscale_generated.py")

if "JSRELOAD" in os.environ and os.path.exists(j.core.application._lib_generation_path):
    print("RELOAD JUMPSCALE LIBS")
    os.remove(j.core.application._lib_generation_path)

generated = False
# print (sys.path)
if not os.path.exists(j.core.application._lib_generation_path):
    print("WARNING: GENERATION OF METADATA FOR JUMPSCALE")
    from .core.generator.JSGenerator import JSGenerator

    j.core.jsgenerator = JSGenerator(j)
    j.core.jsgenerator.generate(methods_find=True)
    j.core.jsgenerator.report()
    generated = True


import jumpscale_generated


if generated and len(j.core.application.errors_init) > 0:
    print("THERE ARE ERRORS: look in /tmp/jumpscale/ERRORS_report.md")
# else:
#     print ("INIT DONE")

# profileStop(pr)


# import time
# time.sleep(1000)
