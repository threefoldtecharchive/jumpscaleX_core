import os
import atexit
import psutil
import traceback


import gc
import sys


class Application(object):
    def __init__(self, j):

        self._j = j

        self._calledexit = False

        self.state = "UNKNOWN"
        self.appname = "UNKNOWN"

        self.logger = None

        self._debug = None

        self._systempid = None

        self.schemas = None

        self.errors_init = []

        self.appname = "unknown"

        self._in_autocomplete = False

        self.exception_handle = self._j.core.myenv.exception_handle
        self._log2fs_session_name = None

    @property
    def appname(self):
        return self._j.core.myenv.appname

    @appname.setter
    def appname(self, val):
        self._j.core.myenv.appname = val

    @property
    def interactive(self):

        return self._j.core.myenv.interactive

    @interactive.setter
    def interactive(self, val):
        self._j.core.myenv.interactive = val

    @property
    def loghandlers(self):
        return self._j.core.myenv.loghandlers

    # @loghandlers.setterkds
    # def loghandlers(self, val):
    #     self._j.core.myenv.loghandlers = val

    @property
    def errorhandlers(self):
        return self._j.core.myenv.errorhandlers

    # @errorhandlers.setter
    # def errorhandlers(self, val):
    #     self._j.core.myenv.errorhandlers = val

    @property
    def bcdb_system(self):
        # try:
        #     self._j.data.nacl.default
        # except Exception as e:
        #     if str(e).find("could not find the path of the private key") != -1:
        #         print("WARNING:cannot find the private key")
        #         self._j.data.nacl.configure()
        #     raise e
        return self._j.data.bcdb.get_system(reset=False)

    def bcdb_system_destroy(self):
        s = self._j.data.bcdb.get_system()
        s.destroy()
        self._bcdb_system = None

    def subprocess_prepare(self):
        self._bcdb_system = None
        self._debug = None
        self._systempid = None
        self._j.core.db_reset(self._j)

        for obj in self.obj_iterator:
            obj._children = self._j.baseclasses.dict()
            obj._obj_cache_reset()
            obj._obj_reset()

    def log2fs_register(self, session_name):
        """
        will write logs with ansi codes to /sandbox/var/log/session_name/$hrtime4session/$hrtime4step_context.ansi

        use less -r to see the logs with color output

        :param session_name: name of the session
        :return:
        """
        self._log2fs_session_name = session_name
        tt = self._j.data.time.getLocalTimeHRForFilesystem()
        self._log2fs_path_prefix = "/sandbox/var/log/%s/%s" % (self._log2fs_session_name, tt)
        self.log2fs_context_change("init")

        os.makedirs(self._log2fs_path_prefix)
        assert self._log2fs_path
        self._j.core.myenv.loghandlers.append(self._log2fs)

    def log2fs_context_change(self, context):
        """

        :param context:
        :return:
        """
        tt = self._j.data.time.getLocalTimeHRForFilesystem()
        self._log2fs_context = context
        self._log2fs_path = "%s/%s_%s.ansi" % (self._log2fs_path_prefix, tt, self._log2fs_context)

    def _log2fs(self, logdict):
        """
        is a log hander for j.core.myenv.loghandlers

        how to use

        if j.core.myenv.loghandlers==[]:


        :param logdict:
        :return:
        """
        if self._log2fs_session_name:
            out = self._j.core.tools.log2str(logdict)
            out = out.rstrip() + "\n"
            try:
                fp = open(self._log2fs_path, "ab")
            except:
                self._j.shell()
                w
            # if self._j.data.types.string.check(contents):
            fp.write(bytes(out, "UTF-8"))
            # else:
            # fp.write(out)
            fp.close()

    # def bcdb_system_configure(self, addr, port, namespace, secret):
    #     """
    #     will remember that this bcdb is being used
    #     will remember in redis (encrypted)
    #     :return:
    #     """
    #     self._j.shell()

    # def _trace_get(self, ttype, err, tb=None):
    #
    #     tblist = traceback.format_exception(ttype, err, tb)
    #
    #     ignore = ["click/core.py", "ipython", "bpython", "loghandler", "errorhandler", "importlib._bootstrap"]
    #
    #     # if self._limit and len(tblist) > self._limit:
    #     #     tblist = tblist[-self._limit:]
    #     tb_text = ""
    #     for item in tblist:
    #         for ignoreitem in ignore:
    #             if item.find(ignoreitem) != -1:
    #                 item = ""
    #         if item != "":
    #             tb_text += "%s" % item
    #     return tb_text

    def _check_debug(self):
        if not "JSGENERATE_DEBUG" in os.environ:
            return False
        if os.environ["JSGENERATE_DEBUG"] in ["1", "Y"]:
            return True
        return False

    # def error_init(self, cat, obj, error, die=True):
    #
    #     print("ERROR: %s:%s" % (cat, obj))
    #     print(error)
    #     trace = self._trace_get(ttype=None, err=error)
    #     self.errors_init.append((cat, obj, error, trace))
    #     if not self._check_debug():
    #         msg = "%s:%s:%s" % (cat, obj, error)
    #         # self.report_errors()
    #         raise j.exceptions.Base(msg)
    #     return "%s:%s:%s" % (cat, obj, error)

    def reset(self):
        """
        empties the core.db
        """
        if self._j.core.db is not None:
            for key in self._j.core.db.keys():
                self._j.core.db.delete(key)
        self.reload()

    def reload(self):
        self._j.tools.jsloader.generate()

    @property
    def debug(self):
        return self._j.core.myenv.debug

    @debug.setter
    def debug(self, value):
        self._j.core.myenv.debug = value

    def debug_set_in_config(self, value=True):
        """
        the std debug is only set in memory, if you want to have on config file use this one
        :return:
        """
        value = j.data.types.bool.clean(value)
        j.core.myenv.config["DEBUG"] = True
        j.core.myenv.config.config_save()

    def break_into_jshell(self, msg="DEBUG NOW"):
        if self.debug is True:
            self._log_debug(msg)
            from IPython import embed

            embed()
        else:
            raise self._j.exceptions.RuntimeError("Can't break into jsshell in production mode.")

    def init(self, **kwargs):
        pass

    @property
    def systempid(self):
        if self._systempid is None:
            self._systempid = os.getpid()
        return self._systempid

    def start(self, name=None):
        """Start the application

        You can only stop the application with return code 0 by calling
        self._j.application.stop(). Don't call sys.exit yourself, don't try to run
        to end-of-script, I will find you anyway!
        """
        if name:
            self.appname = name

        if "JSPROCNAME" in os.environ:
            self.appname = os.environ["JSPROCNAME"]

        if self.state == "RUNNING":
            raise self._j.exceptions.RuntimeError("Application %s already started" % self.appname)

        # Register exit handler for sys.exit and for script termination
        atexit.register(self._exithandler)
        # Set state
        self.state = "RUNNING"

        # self._log_info("***Application started***: %s" % self.appname)

    def stop(self, exitcode=0, stop=True):
        """Stop the application cleanly using a given exitcode

        @param exitcode: Exit code to use
        @type exitcode: number
        """
        import sys

        # TODO: should we check the status (e.g. if application wasnt started,
        # we shouldnt call this method)
        if self.state == "UNKNOWN":
            # Consider this a normal exit
            self.state = "HALTED"
            sys.exit(exitcode)

        # Since we call os._exit, the exithandler of IPython is not called.
        # We need it to save command history, and to clean up temp files used by
        # IPython itself.
        # self._log_debug("Stopping Application %s" % self.appname)
        try:
            __IPYTHON__.atexit_operations()
        except BaseException:
            pass

        self._calledexit = True
        # to remember that this is correct behavior we set this flag

        # tell gridmaster the process stopped

        # TODO: this SHOULD BE WORKING AGAIN, now processes are never removed

        if stop:
            sys.exit(exitcode)

    def _exithandler(self):
        # Abnormal exit
        # You can only come here if an application has been started, and if
        # an abnormal exit happened, i.e. somebody called sys.exit or the end of script was reached
        # Both are wrong! One should call self._j.application.stop(<exitcode>)
        # TODO: can we get the line of code which called sys.exit here?

        # self._self._log_debug("UNCLEAN EXIT OF APPLICATION, SHOULD HAVE USED self._j.application.stop()", 4)
        import sys

        if not self._calledexit:
            self.stop(stop=False)

    # def getCPUUsage(self):
    #     """
    #     try to get cpu usage, if it doesn't work will return 0
    #     By default 0 for windows
    #     """
    #     try:
    #         pid = os.getpid()
    #         if self._j.core.platformtype.myplatform.platform_is_windows:
    #             return 0
    #         if self._j.core.platformtype.myplatform.platform_is_linux:
    #             command = "ps -o pcpu %d | grep -E --regex=\"[0.9]\"" % pid
    #             self._log_debug("getCPUusage on linux with: %s" % command)
    #             exitcode, output, err = self._j.sal.process.execute(
    #                 command, True, False)
    #             return output
    #         elif self._j.core.platformtype.myplatform.isSolaris():
    #             command = 'ps -efo pcpu,pid |grep %d' % pid
    #             self._log_debug("getCPUusage on linux with: %s" % command)
    #             exitcode, output, err = self._j.sal.process.execute(
    #                 command, True, False)
    #             cpuUsage = output.split(' ')[1]
    #             return cpuUsage
    #     except Exception:
    #         pass
    #     return 0

    def getMemoryUsage(self):
        """
        for linux is the unique mem used for this process
        is in KB
        """
        p = psutil.Process()
        info = p.memory_full_info()
        return info.uss / 1024

    def getProcessObject(self):
        return self._j.sal.process.getMyProcessObject()

    #
    # def reload(self):
    #     # from importlib import reload
    #     from IPython.lib.deepreload import reload as dreload
    #     l=[]
    #     for name,group in self._j.core._groups.items():
    #         for key,obj in group.__dict__.items():
    #             if obj is not None:
    #                 print("GROUP_OBJ:%s"%key)
    #                 self._walk_obj(obj)
    #                 print("POP:%s"%key)
    #                 del group.__dict__[key]
    #                 group.__dict__[key]=None
    #
    #     res=[]
    #     for key,mod in sys.modules.items():
    #         s=str(mod).lower()
    #         if s.find("jumpscale")!=-1 and s.find("_init")==-1 and s.find("/core/")==-1 and s.find("jumpscale_generated")==-1:
    #             res.append(key)
    #
    #     for key in res:
    #         self._j.shell()
    #
    #         try:
    #             dreload(sys.modules[key])
    #         except:
    #             print("could not reload:%s"%key)
    #         # print("module delete:%s"%key)
    #         # del sys.modules[key]
    #         # exec("del %s"%key)
    #         # sys.modules.pop(key)

    @property
    def obj_iterator(self):
        """
        iterates over all loaded objects in kosmos space (which inherits of JSBase class)
        e.g.
        objnames = [i._classname,for i in j.application.obj_iterator]

        :return:
        """
        for item in self._iterate_rootobj():
            if isinstance(item, self._j.baseclasses.object):
                yield item
                for item in item._children_recursive_get():
                    yield item

    def _iterate_rootobj(self, obj=None):
        if obj is None:
            for key, item in self._j.__dict__.items():
                if key.startswith("_"):
                    continue
                if key in ["exceptions", "core", "dirs", "application", "data_units", "errorhandler"]:
                    continue
                # self._j.core.tools.log("iterate jumpscale factory:%s"%key)
                for key2, item2 in item.__dict__.items():
                    # self._j.core.tools.log("iterate rootobj:%s"%key2)
                    if item2 is not None:
                        # self._j.core.tools.log("yield obj:%s"%item2._key)
                        yield item2

    #
    # def _get_referents(self,obj,level=0,done=[]):
    #     if isinstance(obj, types.FunctionType) or isinstance(obj, types.MethodType):
    #         return done
    #     level+=1
    #     try:
    #         r=str(obj)
    #     except:
    #         r="unknown"
    #     r.replace("\n","")
    #     if len(r)>120:
    #         r=r[:120]
    #
    #     for item in gc.get_referents(obj):
    #         if item is not None and item not in done:
    #             done.append(item)
    #             done = self._get_referents(item,level=level,done=done)
    #     if hasattr(obj,"_obj_cache_reset"):
    #         print("%s: empty %s"%(level,r))
    #         obj._obj_cache_reset()
    #
    #     return done

    def _setWriteExitcodeOnExit(self, value):
        if not self._j.data.types.bool.check(value):
            raise j.exceptions.Value
        self._writeExitcodeOnExit = value

    def _getWriteExitcodeOnExit(self):
        if not hasattr(self, "_writeExitcodeOnExit"):
            return False
        return self._writeExitcodeOnExit

    writeExitcodeOnExit = property(
        fset=_setWriteExitcodeOnExit,
        fget=_getWriteExitcodeOnExit,
        doc="Gets / sets if the exitcode has to be persisted on disk",
    )

    def _gc_count(self):
        return len(gc.get_objects())
        # cs=gc.get_count()
        # res=0
        # for c in cs:
        #     res+=c
        # return res

    # def _test_gc(self):
    #     """
    #     kosmos 'j.application._test_gc()'
    #     :return:
    #     """
    #     j=self._j
    #     print ("nr of obj in gc at start: %s" % self._gc_count())
    #     print ("mem usage start:%s"% self.getMemoryUsage())
    #     o=j.clients.ssh.instances.kds
    #     print ("mem usage after 1 config obj:%s"% self.getMemoryUsage())
    #     print ("nr of obj before garbage collection: %s"%self._gc_count())
    #     del o
    #     o="a"
    #     self.reload()
    #     print ("mem usage after 1 config obj:%s"% self.getMemoryUsage())
    #     print ("nr of obj after garbage collection: %s"%self._gc_count())
    #
    #     self._j.shell()
    #

    def check(self, generate=False):
        """
        jsx check
        :param generate:
        :return:
        """
        j = self._j

        if generate:
            self.generate()

        try:
            j.data.nacl.default
        except Exception as e:
            if str(e).find("could not find the path of the private key") != -1:
                print("WARNING:cannot find the private key")
                j.data.nacl.configure()
            raise e

        def decrypt():
            try:
                j.data.nacl.default.signing_key
                j.data.nacl.default.private_key.public_key.encode()
                return True
            except Exception as e:
                if str(e).find("jsx check") != -1:
                    print("COULD NOT DECRYPT THE PRIVATE KEY, COULD BE SECRET KEY IS WRONG, PLEASE PROVIDE NEW ONE.")
                    if j.tools.console.askYesNo("Ok to change the stored private key?"):
                        j.core.myenv.config["SECRET"] = ""
                    j.core.myenv.secret_set()
                    return False
                raise e
            return False

        while not decrypt():
            pass

        try:
            j.application.bcdb_system
        except Exception as e:
            if str(e).find("Ciphertext failed") != -1:
                print("COULD NOT GET DATA FROM BCDB, PROB ENCRYPTED WITH OTHER PRIVATE KEY AS WHAT IS NOW ON SYSTEM")
                sys.exit(1)
            if str(e).find("cannot be decrypted") != -1:
                print("COULD NOT DECRYPT THE METADATA FOR BCDB, DIFFERENT ENCRYPTION KEY USED")
                if j.tools.console.askYesNo("Ok to delete this metadata, will prob be rebuild"):
                    j.sal.fs.remove(j.core.tools.text_replace("{DIR_CFG}/bcdb_config"))
                    j.application.bcdb_system

        j.data.bcdb.check()

    def generate(self, path=None):
        j = self._j
        j.sal.fs.remove("{DIR_VAR}/codegen")
        j.sal.fs.remove("{DIR_VAR}/cmds")
        from Jumpscale.core.generator.JSGenerator import JSGenerator
        from Jumpscale import j

        g = JSGenerator(j)

        if path:
            # means we need to link
            g.lib_link(path)
        g.generate(methods_find=True)
        g.report()
