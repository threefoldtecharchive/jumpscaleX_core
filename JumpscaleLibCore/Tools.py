from __future__ import unicode_literals
import copy
import msgpack
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

from fcntl import F_GETFL, F_SETFL, fcntl
from os import O_NONBLOCK
from pathlib import Path
from subprocess import Popen
import inspect
import json
import traceback
import pudb

import pygments
from pygments import formatters
from pygments import lexers

pygments_formatter = formatters.get_formatter_by_name("terminal")
pygments_pylexer = lexers.get_lexer_by_name("python")

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
        raise self.exceptions.Value("incredible error",cat="firebrigade.ghent",data=data,exception=e)

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
                raise self.exceptions.JSBUG("level needs to be int or str", data=locals())
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
            return self._data_serializer_safe(self.logdict)
        else:
            return self.message

    def __repr__(self):
        if not self.logdict:
            raise self.exceptions.JSBUG("logdict not known (is None)")
        print(self.log2str(self.logdict))
        return ""


class InputError(Exception):
    pass


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
    def __init__(self, myenv):

        self.myenv = myenv

        self._supported_editors = ["micro", "mcedit", "joe", "vim", "vi"]  # DONT DO AS SET  OR ITS SORTED
        self._shell = None
        self.custom_log_printer = None

        self.exceptions = JSExceptions()

        # self.formatter = OurTextFormatter()

    def traceback_list_format(self, tb):
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
                        self.shell()
                        raise self.exceptions.Base()
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
                    self.shell()
                else:
                    llocals = None
                tb_item = [item.filename, item.name, item.lineno, item.line, llocals]
                res.append(tb_item)
        return res

    def get_repos_info(self):
        return self.myenv.GITREPOS

    def traceback_text_get(self, tb=None, stdout=False):
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
                self.pprint(line2, end="", log=False)
                print(pygments.highlight(item.line, pygments_pylexer, pygments_formatter).rstrip())

            out += "%s\n" % line
        return out

    def _traceback_filterLocalsself(self, k, v):
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
        raise self.exceptions.Base()

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
        if self.myenv.pygmentsObj:
            self.myenv.pygmentsObj
            # style=pygments.styles.get_style_by_name("vim")
            formatter = pygments.formatters.Terminal256Formatter()
            lexer = pygments.lexers.get_lexer_by_name("pytb", stripall=True)  # pytb
            tb_colored = pygments.highlight(tb_text, lexer, formatter)
            sys.stderr.write(tb_colored)
            # print(tb_colored)
        else:
            sys.stderr.write(tb_text)

    def log(
        self,
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
        if self.myenv.debug or level > 39:  # error+ is shown
            stdout = True

        if isinstance(msg, Exception):
            raise self.exceptions.JSBUG("msg cannot be an exception raise by means of exception=... in constructor")

        # first deal with traceback
        if exception and not tb:
            # if isinstance(exception, BaseJSException):
            if hasattr(exception, "_exc_traceback"):
                tb = exception._exc_traceback
            else:
                extype_, value_, tb = sys.exc_info()

        linenr = None
        if tb:
            logdict["traceback"] = self.traceback_list_format(tb)
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
            if isinstance(exception, self.exceptions.Base):
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
                        + self.text_indent(msg, 4).rstrip()
                        + "\n"
                        + self.text_indent(msg_e, 4)
                        + "{RESET}"
                    )
                else:
                    msg = "EXCEPTION: \n" + self.text_indent(msg, 4).rstrip() + "\n" + self.text_indent(msg_e, 4)

            else:
                if stdout:
                    msg = "{RED}EXCEPTION: \n" + self.text_indent(msg_e, 4).rstrip() + "{RESET}"
                else:
                    msg = "EXCEPTION: \n" + self.text_indent(msg_e, 4).rstrip()
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
                        exception = self.text_indent(exception.exception, 6)
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
                data = self._data_serializer_safe(data)

        logdict["data"] = data
        if stdout:
            logdict = copy.copy(logdict)
            self.log2stdout(logdict, data_show=data_show)
        elif level > 14:
            self.log2stdout(logdict, data_show=False, enduser=True)

        iserror = tb or exception
        return self.process_logdict_for_handlers(logdict, iserror)

    def process_logdict_for_handlers(self, logdict, iserror=True):
        """

        :param logdict:
        :param iserror:   if error will use self.myenv.errorhandlers: allways self.myenv.loghandlers
        :return:
        """

        assert isinstance(logdict, dict)

        if iserror:
            for handler in self.myenv.errorhandlers:
                handler(logdict)

        else:

            for handler in self.myenv.loghandlers:
                try:
                    handler(logdict)
                except Exception as e:
                    self.myenv.exception_handle(e)

        return logdict

    def method_code_get(self, method, **kwargs):
        """

        :param method: the method to get the code from
        :param kwargs: will be replaced in {} template args in the method
        :return:   (methodname,code)
        """
        assert callable(method)
        code = inspect.getsource(method)
        code2 = self.text_strip(code)
        code3 = code2.replace("self,", "").replace("self ,", "").replace("self  ,", "")

        if kwargs:
            code3 = self.text_replace(code3, text_strip=False, args=kwargs)

        methodname = ""
        for line in code3.split("\n"):
            line = line.strip()
            if line.startswith("def "):
                methodname = line.split("(", 1)[0].strip().replace("def ", "")
                break

        if methodname == "":
            raise Exception("defname cannot be empty")

        return methodname, code3

    def _cmd_check(self, command, original_command=None):
        if not command:
            return
        if command.find("{DIR_") != -1:
            if original_command:
                print("COMMAND WAS:\n%s" % command)
                raise self.exceptions.Input(
                    "cannot execute found template var\ncmd:%s\n%s" % (original_command, command)
                )
            else:
                raise self.exceptions.Input("cannot execute found template var\ncmd:%s" % command)

    def _execute(
        self,
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
            executor = self.myenv

        if executor.debug:
            showout = True

        if executor.debug or log:
            self.log("execute:%s" % command)
            if original_command:
                self.log("execute_original:%s" % original_command)

        self._cmd_check(command, original_command)
        rc = 1
        counter = 0
        while rc > 0 and counter < retry:
            if interactive:
                rc, out, err = self._execute_interactive(cmd=command)
            else:
                rc, out, err = self._execute_process(
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
                self.log("redo cmd", level=30)
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
                msg += self.text_indent(command).rstrip() + "\n\n"
            if out.strip() != "":
                msg += "stdout:\n"
                msg += self.text_indent(out).rstrip() + "\n\n"
            if err.strip() != "":
                msg += "stderr:\n"
                msg += self.text_indent(err).rstrip() + "\n\n"
            raise self.exceptions.Base(msg)

        return rc, out, err

    def _execute_process(
        self, command, die=True, env=None, cwd=None, useShell=True, async_=False, showout=True, timeout=3600
    ):

        os.environ["PYTHONUNBUFFERED"] = "1"  # WHY THIS???

        # if hasattr(subprocess, "_mswindows"):
        #     mswindows = subprocess._mswindows
        # else:
        #     mswindows = subprocess.mswindows

        self._cmd_check(command)

        if "'" in command:
            self.file_write("/tmp/script_exec_process.sh", command)
            command = "sh -ex /tmp/script_exec_process.sh"

        if env is None or env == {}:
            env = os.environ

        if useShell:
            p = Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=self.myenv.platform_is_unix,
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
                close_fds=self.myenv.platform_is_unix,
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
            if self.myenv.platform_is_unix:
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
                        self.pprint(line, end="")

                # Fold cache and return
                return "".join(data)

            else:
                # This is not UNIX, most likely Win32. read() seems to work
                def readout(stream):
                    line = stream.read().decode()
                    if showout:
                        # self.log(line)
                        self.pprint(line, end="")

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
                raise self.exceptions.Base("prob bug, needs to think this through, seen the while loop")
            while p.poll() is None:
                # means process is still running

                time.sleep(0.01)
                now = time.time()
                # print("wait")

                if timeout != 0 and now > end:
                    if self.myenv.platform_is_unix:
                        # Soft and hard kill on Unix
                        try:
                            p.terminate()
                            # Give the process some time to settle
                            time.sleep(0.2)
                            p.kill()
                            raise self.exceptions.Timeout(f"command: '{command}' timed out after {timeout} seconds")
                        except OSError:
                            pass
                    else:
                        # Kill on anything else
                        time.sleep(0.1)
                        if p.poll():
                            p.terminate()
                    if self.myenv.debug or showout:
                        self.log("process killed because of timeout", level=30)
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

    def _execute_interactive(self, cmd=None):
        """
        @return returncode,stdout,sterr
        """
        # if "'" in cmd or cmd.startswith("source") or "&" in cmd:
        self.file_write("/tmp/script_exec_interactive.sh", cmd)
        self._cmd_check(cmd)
        cmd = "bash -e /tmp/script_exec_interactive.sh"
        returncode = os.system(cmd)
        # args = cmd.split(" ")
        # args[0] = shutil.which(args[0])
        # returncode = os.spawnlp(os.P_WAIT, args[0], *args)
        # cmd = " ".join(args)
        if returncode == 127:
            raise self.exceptions.Base("{}: command not found\n".format(cmd))
        return returncode, "", ""

    def file_touch(self, path):
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)

        with open(path, "a"):
            os.utime(path, None)

    def file_edit(self, path):
        """
        starts the editor micro with file specified
        """
        user_editor = os.environ.get("EDITOR")
        if user_editor and self.cmd_installed(user_editor):
            self._execute_interactive("%s %s" % (user_editor, path))
            return
        for editor in self._supported_editors:
            if self.cmd_installed(editor):
                self._execute_interactive("%s %s" % (editor, path))
                return
        raise self.exceptions.Base("cannot edit the file: '{}', non of the supported editors is installed".format(path))

    def file_write(self, path, content, replace=False, args=None):
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
                content = self.text_replace(content, args=args)
            p.write_text(content)
        else:
            p.write_bytes(content)

    def file_append(self, path, content):
        dirname = os.path.dirname(path)
        try:
            os.makedirs(dirname, exist_ok=True)
        except FileExistsError:
            pass
        my_path = Path(path)
        with my_path.open("a") as f:
            f.write(content)

    def file_text_read(self, path):
        path = self.text_replace(path)
        p = Path(path)
        try:
            return p.read_text()
        except Exception as e:
            self.shell()

    def file_read(self, path):
        path = self.text_replace(path)
        p = Path(path)
        try:
            return p.read_bytes()
        except Exception as e:
            self.shell()

    def dir_ensure(self, path, remove_existing=False):
        """Ensure the existance of a directory on the system, if the
        Directory does not exist, it will create

        :param path:path of the directory
        :type path: string
        :param remove_existing: If True and the path already exist,
            the existing path will be removed first, defaults to False
        :type remove_existing: bool, optional
        """

        path = self.text_replace(path)

        if os.path.exists(path) and remove_existing is True:
            self.delete(path)
        elif os.path.exists(path):
            return
        os.makedirs(path)

    def link(self, src, dest, chmod=None):
        """

        :param src: is where the link goes to
        :param dest: is where he link will be
        :param chmod e.g. 770
        :return:
        """
        src = self.text_replace(src)
        dest = self.text_replace(dest)
        self.execute("rm -f %s" % dest)
        self.execute("ln -s {} {}".format(src, dest))
        if chmod:
            self.execute("chmod %s %s" % (chmod, dest))

    def delete(self, path):
        """Remove a File/Dir/...
        @param path: string (File path required to be removed)
        """
        path = self.text_replace(path)
        if self.myenv.debug:
            self.log("Remove file with path: %s" % path)
        if os.path.islink(path):
            os.unlink(path)
        if not self.exists(path):
            return

        mode = os.stat(path).st_mode
        if os.path.isfile(path) or stat.S_ISSOCK(mode):
            if len(path) > 0 and path[-1] == os.sep:
                path = path[:-1]
            os.remove(path)
        else:
            shutil.rmtree(path)

    def path_parent(self, path):
        """
        Returns the parent of the path:
        /dir1/dir2/file_or_dir -> /dir1/dir2/
        /dir1/dir2/            -> /dir1/
        """
        # TODO: needs to be replaced by using pathlib everywhere
        parts = path.split(os.sep)
        if parts[-1] == "":
            parts = parts[:-1]
        parts = parts[:-1]
        if parts == [""]:
            return os.sep
        return os.sep.join(parts)

    def exists(self, path, followlinks=True):
        """Check if the specified path exists
        @param path: string
        @rtype: boolean (True if path refers to an existing path)
        """
        if path is None:
            raise self.exceptions.Value("Path is not passed in system.fs.exists")
        found = False
        try:
            st = os.lstat(path)
            found = True
        except (OSError, AttributeError):
            pass
        if found and followlinks and stat.S_ISLNK(st.st_mode):
            if self.myenv.debug:
                self.log("path %s exists" % str(path.encode("utf-8")))
            linkpath = os.readlink(path)
            if linkpath[0] != "/":
                linkpath = os.path.join(self.path_parent(path), linkpath)
            return self.exists(linkpath)
        if found:
            return True
        # self.log('path %s does not exist' % str(path.encode("utf-8")))
        return False

    def _installbase_for_shell(self):

        if "darwin" in self.myenv.platform():

            script = """
            pip3 install ipython==7.5.0 ptpython==2.0.4 prompt-toolkit==2.0.9 --force-reinstall
            pip3 install pudb
            pip3 install pygments
            """
            self.execute(script, interactive=True)

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
            if self.DockerFactory().indocker():
                sudoremove = True
            else:
                sudoremove = False
            self.execute(script, interactive=True, sudo_remove=sudoremove)

    def clear(self):
        print(chr(27) + "[2j")
        print("\033c")
        print("\x1bc")

    def shell(self, loc=True):

        if loc:
            import inspect

            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            f = calframe[1]
        else:
            f = None
        if self._shell is None:

            try:
                from IPython.terminal.embed import InteractiveShellEmbed
            except Exception as e:
                print("NEED TO INSTALL BASICS FOR DEBUG SHELL SUPPORT")
                self._installbase_for_shell()
                from IPython.terminal.embed import InteractiveShellEmbed
            if f:
                print("\n*** file: %s" % f.filename)
                print("*** function: %s [linenr:%s]\n" % (f.function, f.lineno))

            self._shell = InteractiveShellEmbed(banner1="", exit_msg="")
            self._shell.Completer.use_jedi = False

        return self._shell(stack_depth=2)

    #
    # def shell(loc=True,exit=True):
    #     if loc:
    #         import inspect
    #         curframe = inspect.currentframe()
    #         calframe = inspect.getouterframes(curframe, 2)
    #         f = calframe[1]
    #         print("\n*** file: %s"%f.filename)
    #         print("*** function: %s [linenr:%s]\n" % (f.function,f.lineno))
    #     from ptpython.repl import embed
    #     self.clear()
    #     history_filename="~/.jsx_history"
    #     if not self.exists(history_filename):
    #         self.file_write(history_filename,"")
    #     ptconfig = None
    #     if exit:
    #         sys.exit(embed(globals(), locals(),configure=ptconfig,history_filename=history_filename))
    #     else:
    #         embed(globals(), locals(),configure=ptconfig,history_filename=history_filename)

    def text_strip(
        self, content, ignorecomments=False, args={}, replace=False, executor=None, colors=False, die_if_args_left=False
    ):
        """
        remove all spaces at beginning & end of line when relevant (this to allow easy definition of scripts)
        args will be substitued to .format(...) string function https://docs.python.org/3/library/string.html#formatspec
        self.myenv.config will also be given to the format function


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
            content = self.text_replace(
                content=content, args=args, executor=executor, text_strip=False, die_if_args_left=die_if_args_left
            )
        else:
            if colors and "{" in content:
                for key, val in self.myenv.MYCOLORS.items():
                    content = content.replace("{%s}" % key, val)

        return content

    def bool(self, txt):
        if not txt:
            return False
        txt = str(txt).lower().strip()
        if txt in ["true", "1", "yes"]:
            return True
        return False

    def text_strip_to_ascii_dense(self, text):
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

    def text_replace(
        self,
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

        self.text_replace

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
            raise self.exceptions.Input("content needs to be str")

        if args is None:
            args = {}

        if not "{" in content:
            return content

        if executor:
            content2 = self.args_replace(
                content,
                # , executor.info.cfg_jumpscale
                args_list=(args, executor.config),
                ignorecolors=ignorecolors,
                die_if_args_left=die_if_args_left,
                primitives_only=primitives_only,
            )
        else:
            content2 = self.args_replace(
                content,
                args_list=(args, self.myenv.config),
                ignorecolors=ignorecolors,
                die_if_args_left=die_if_args_left,
                primitives_only=primitives_only,
            )

        if text_strip:
            content2 = self.text_strip(content2, ignorecomments=ignorecomments, replace=False)

        return content2

    def args_replace(self, content, args_list=None, primitives_only=False, ignorecolors=False, die_if_args_left=False):
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
                return self._data_serializer_safe(val)

        def args_combine():
            args_new = {}
            for replace_args in args_list:
                for key, val in replace_args.items():
                    if key not in args_new:
                        val = arg_process(key, val)
                        if val:
                            args_new[key] = val

            for field_name in self.myenv.MYCOLORS:
                if ignorecolors:
                    args_new[field_name] = ""
                else:
                    args_new[field_name] = self.myenv.MYCOLORS[field_name]

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
                items = [i for i in self.formatter.parse(line)]
            except Exception as e:
                return process_line_failback(line)

            do = {}

            for literal_text, field_name, format_spec, conversion in items:
                if not field_name:
                    continue
                if field_name in self.myenv.MYCOLORS:
                    if ignorecolors:
                        do[field_name] = ""
                    else:
                        do[field_name] = self.myenv.MYCOLORS[field_name]
                for args in args_list:
                    if field_name in args:
                        do[field_name] = arg_process(field_name, args[field_name])
                if field_name not in do:
                    if die_if_args_left:
                        raise self.exceptions.Input("could not find:%s in line:%s" % (field_name, line))
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

    def _data_serializer_safe(self, data):
        if isinstance(data, dict):
            data = data.copy()  # important to have a shallow copy of data so we don't change original
            for key in ["passwd", "password", "secret"]:
                if key in data:
                    data[key] = "***"
        elif isinstance(data, int) or isinstance(data, str) or isinstance(data, list):
            return str(data)

        serialized = serializer(data)
        res = self.text_replace(content=serialized, ignorecolors=True)
        return res

    def log2stdout(self, logdict, data_show=False, enduser=False):
        def show():
            # always show in debugmode and critical
            if self.myenv.debug or (logdict and logdict["level"] >= 50):
                return True
            if not self.myenv.log_console:
                return False
            return logdict and (logdict["level"] >= self.myenv.log_level)

        if not show() and not data_show:
            return

        if enduser:
            if "public" in logdict and logdict["public"]:
                msg = logdict["public"]
            else:
                msg = logdict["message"]
            if logdict["level"] > 29:
                print(self.text_replace("{RED} * %s{RESET}\n" % msg))
            else:
                print(self.text_replace("{YELLOW} * %s{RESET}\n" % msg))
            return

        text = self.log2str(logdict, data_show=True, replace=True)
        p = print
        if self.myenv.config.get("LOGGER_PANEL_NRLINES"):
            if self.custom_log_printer:
                p = self.custom_log_printer
        try:
            p(text)
        except UnicodeEncodeError as e:
            text = text.encode("ascii", "ignore")
            p(text)

    def traceback_format(self, tb, replace=True):
        """format traceback

        :param tb: traceback
        :type tb: traceback object or a formatted list
        :return: formatted trackeback
        :rtype: str
        """
        if not isinstance(tb, list):
            tb = self.traceback_list_format(tb)

        out = self.text_replace("\n{RED}--TRACEBACK------------------{RESET}\n")
        for tb_path, tb_name, tb_lnr, tb_line, tb_locals in tb:
            C = "{GREEN}{tb_path}{RESET} in {BLUE}{tb_name}{RESET}\n"
            C += "    {GREEN}{tb_lnr}{RESET}    {tb_code}{RESET}"
            tb_code = pygments.highlight(tb_line, pygments_pylexer, pygments_formatter).rstrip()
            tbdict = {"tb_path": tb_path, "tb_name": tb_name, "tb_lnr": tb_lnr, "tb_code": tb_code}
            C = self.text_replace(C.lstrip(), args=tbdict, text_strip=True)
            out += C.rstrip() + "\n"
        out += self.text_replace("{RED}-----------------------------\n{RESET}")
        return out

    def log2str(self, logdict, data_show=True, replace=True):
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
        logdict["TIME"] = time.strftime(self.myenv.FORMAT_TIME, timetuple)

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

        LOGFORMAT = self.myenv.LOGFORMAT[LOGLEVEL]

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
            out += self.text_replace("{RED}--SOURCE: %s-20--{RESET}\n" % logdict["source"])

        msg = self.text_replace(LOGFORMAT, args=logdict, die_if_args_left=False).rstrip()
        out += msg

        if "traceback" in logdict and logdict["traceback"]:
            out += self.traceback_format(logdict["traceback"])

        if data_show:
            if logdict["data"] != None:
                if isinstance(logdict["data"], dict):
                    try:
                        data = serializer(logdict["data"])
                    except Exception as e:
                        data = logdict["data"]
                else:
                    data = logdict["data"]
                data = self.text_indent(data, 2, strip=True)
                out += self.text_replace("\n{YELLOW}--DATA-----------------------\n")
                out += data.rstrip() + "\n"
                out += self.text_replace("-----------------------------{RESET}\n")

        if logdict["level"] > 39:
            # means is error
            if "public" in logdict and logdict["public"]:
                out += "{YELLOW}" + self.text_indent(logdict["public"].rstrip(), nspaces=2, prefix="* ") + "{RESET}\n\n"

        # restore the logdict
        logdict.pop("TIME")
        logdict.pop("filename")

        if replace:
            out = self.text_replace(out)
            if out.find("{RESET}") != -1:
                self.shell()

        return out

    def pprint(
        self, content, ignorecomments=False, text_strip=False, args=None, colors=True, indent=0, end="\n", log=True
    ):
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
            content = self.text_replace(
                content, args=args, text_strip=text_strip, ignorecomments=ignorecomments, die_if_args_left=False
            )
            for key, val in self.myenv.MYCOLORS.items():
                content = content.replace("{%s}" % key, val)
        elif content.find("{RESET}") != -1:
            for key, val in self.myenv.MYCOLORS.items():
                content = content.replace("{%s}" % key, val)

        if indent > 0:
            content = self.text_indent(content)
        if log:
            self.log(content, level=15, stdout=False)

        try:
            print(content, end=end)
        except UnicodeEncodeError as e:
            content = content.encode("ascii", "ignore")
            print(content)

    def text_md5(self, txt: str):
        import hashlib

        if isinstance(txt, str):
            txt2 = txt.encode("utf-8")
        impl = hashlib.new("md5", data=txt2)
        return impl.hexdigest()

    def text_indent(self, content, nspaces=4, wrap=120, strip=True, indentchar=" ", prefix=None, args=None):
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
            raise self.exceptions.Base("content cannot be None")
        if content == "":
            return content
        if not prefix:
            prefix = ""
        content = str(content)
        if args is not None:
            content = self.text_replace(content, args=args)
        if strip:
            content = self.text_strip(content, replace=False)
        if wrap > 0:
            content = self.text_wrap(content, wrap)

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

    def text_wrap(self, txt, length=120):
        out = ""
        for line in txt.split("\n"):
            out += textwrap.fill(line, length, subsequent_indent="    ") + "\n"
        return out

    def _file_path_tmp_get(self, ext="sh"):
        ext = ext.strip(".")
        return self.text_replace("/tmp/jumpscale/scripts/{RANDOM}.{ext}", args={"RANDOM": self._random(), "ext": ext})

    def _random(self):
        return str(random.getrandbits(16))

    def get_envars(self):
        envars = dict()
        content = self.file_read("/proc/1/environ").strip("\x00").split("\x00")
        for item in content:
            k, v = item.split("=")
            envars[k] = v
        return envars

    def execute_jumpscale(self, cmd, die=True):
        self.execute(cmd, jumpscale=True, die=die)

    def _script_process_jumpscale(self, script, env={}, debug=False, interactive=None):
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

        script = self._script_process_python(script, env=env)

        return script

    def _script_process_python(self, script, env={}):
        pre = ""

        if env != {}:
            for key, val in env.items():
                pre += "%s = %s\n" % (key, val)

        if pre:
            script = "%s\n%s" % (pre, script)

        return script

    def _script_process_bash(self, script, die=True, env={}, sudo=False, debug=False):

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

    def _cmd_process(
        self,
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

        cmd = self.text_strip(cmd)

        assert sudo is None or sudo is False  # not implemented yet
        if env is None:
            env = {}

        if self.exists(cmd):
            ext = os.path.splitext(cmd)[1].lower()
            cmd = self.file_read(cmd)
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
                    script = self._script_process_jumpscale(
                        script=script, env=env, debug=debug, interactive=interactive
                    )
                    cmd = "source {DIR_BASE}/env.sh && python3 %s" % dest
                else:
                    script = self._script_process_python(script, env=env)
                    cmd = "source {DIR_BASE}/env.sh && python3 %s" % dest
            else:
                dest = "/tmp/script_%s.sh" % name
                if die:
                    cmd = "bash -e %s" % dest
                else:
                    cmd = "bash %s" % dest
                script = self._script_process_bash(script, die=die, env=env, debug=debug)

            if replace:
                script = self.text_replace(script, args=env, executor=executor)
            if executor:
                executor.file_write(dest, script)
            else:
                self.file_write(dest, script)

            # if self.myenv.debug:
            #     self.log(script)

        if replace:
            cmd = self.text_replace(cmd, args=env, executor=executor)

        self._cmd_check(cmd)
        self._cmd_check(script)

        return dest, cmd

    def execute(
        self,
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

        if callable(command):
            method_name, command = self.method_code_get(command, **args)
            kwargs = None
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

        tempfile, command = self._cmd_process(
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
            raise self.exceptions.Input("Found { in %s" % command)

        r = self._execute(
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
            self.delete(tempfile)
        return r

    def process_pids_get_by_filter(self, filterstr, excludes=[]):
        cmd = "ps ax | grep '%s'" % filterstr
        rcode, out, err = self.execute(cmd)
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

    def process_kill_by_pid(self, pid):
        self.execute("kill -9 %s" % pid)

    def process_kill_by_by_filter(self, filterstr):
        for pid in self.process_pids_get_by_filter(filterstr):
            self.process_kill_by_pid(pid)

    def ask_choices(self, msg, choices=[], default=None):
        self._check_interactive()
        msg = self.text_strip(msg)
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

    def ask_yes_no(self, msg, default="y"):
        """

        :param msg: the msg to show when asking for y or no
        :return: will return True if yes
        """
        self._check_interactive()
        return self.ask_choices(msg, "y,n", default=default) in ["y", ""]

    def _check_interactive(self):
        if not self.myenv.interactive:
            raise self.exceptions.Base("Cannot use console in a non interactive mode.")

    def ask_password(self, question="give secret", confirm=True, regex=None, retry=-1, validate=None, emptyok=False):
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
        self._check_interactive()

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
        raise self.exceptions.Base(
            "Console.askPassword() failed: tried %s times but user didn't fill out a value that matches '%s'."
            % (retry, regex)
        )

    def ask_string(self, msg, default=None):
        self._check_interactive()
        msg = self.text_strip(msg)
        print(msg)
        if "\n" in msg:
            print()
        txt = input()
        if default and txt.strip() == "":
            txt = default
        return txt

    def cmd_installed(self, name):
        if not name in self.myenv._cmd_installed:
            self.myenv._cmd_installed[name] = shutil.which(name) != None
        return self.myenv._cmd_installed[name]

    def cmd_args_get(self):
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

    def tcp_port_connection_test(self, ipaddr, port, timeout=None):
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

    def _code_location_get(self, account, repo):
        """
        accountdir will be created if it does not exist yet
        :param repo:
        :param static: static means we don't use git

        :return: repodir_exists,foundgit, accountdir,repodir

            foundgit means, we found .git in the repodir
            dontpull means, we found .dontpull in the repodir, means code is being synced to the repo from remote, should not update

        """

        prefix = "code"
        if "DIR_CODE" in self.myenv.config:
            accountdir = os.path.join(self.myenv.config["DIR_CODE"], "github", account)
        else:
            accountdir = os.path.join(self.myenv.config["DIR_BASE"], prefix, "github", account)
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

    def code_changed(self, path):
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
        rc, out, err = self.execute(S, showout=False, die=False, args=args)
        return rc > 0

    def code_git_rewrite_url(self, url="", login=None, passwd=None, ssh="auto"):
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
                ssh = self.myenv.available
            except:
                ssh = False
        elif ssh or ssh is False:
            pass
        else:
            raise self.exceptions.Base("ssh needs to be auto, first or True or False: here:'%s'" % ssh)

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
            raise self.exceptions.Base(
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

    def code_gitrepo_args(self, url="", dest=None, login=None, passwd=None, reset=False, ssh="auto"):
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
                raise self.exceptions.Base("dest cannot be None (url is also '')")
            if not self.exists(dest):
                raise self.exceptions.Base(
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
        ) = self.code_git_rewrite_url(url=url, login=login, passwd=passwd, ssh=ssh)

        repository_type = repository_host.split(".")[0] if "." in repository_host else repository_host

        codeDir = self.myenv.config["DIR_CODE"]

        if not dest:
            dest = "%(codedir)s/%(type)s/%(account)s/%(repo_name)s" % {
                "codedir": codeDir,
                "type": repository_type.lower(),
                "account": repository_account.lower(),
                "repo_name": repository_name,
            }

        if reset:
            self.delete(dest)

        return repository_host, repository_type, repository_account, repository_name, dest, repository_url, port

    def code_giturl_parse(self, url):
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
        ) = self.code_git_rewrite_url(url=url)
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

        a, b, c, d, dest, e, port = self.code_gitrepo_args(url)

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

    def code_github_get(self, url, rpath=None, branch=None, pull=False, reset=False):
        """

        :param repo:
        :param account:
        :param branch: falls back to the default branch on self.myenv.DEFAULT_BRANCH
                    if needed, when directory exists and pull is False will not check branch
        :param pull:
        :param reset:
        :return:
        """

        def getbranch(args):
            cmd = "cd {REPO_DIR}; git branch | grep \* | cut -d ' ' -f2"
            rc, stdout, err = self.execute(cmd, die=False, args=args, interactive=False, die_if_args_left=True)
            if rc > 0:
                self.shell()
            current_branch = stdout.strip()
            self.log("Found branch: %s" % current_branch)
            return current_branch

        def checkoutbranch(args, branch):
            args["BRANCH"] = branch
            current_branch = getbranch(args=args)
            if current_branch != branch:
                script = """
                set -e
                cd {REPO_DIR}
                git checkout {BRANCH} -f
                """
                rc, out, err = self.execute(
                    script, die=False, args=args, showout=True, interactive=False, die_if_args_left=True
                )
                if rc > 0:
                    return False

            return True

        (host, type, account, repo, url2, branch2, gitpath, path, port) = self.code_giturl_parse(url=url)
        if rpath:
            path = rpath
        assert "/" not in repo

        if branch is None:
            branch = branch2
        elif isinstance(branch, str):
            if "," in branch:
                raise self.exceptions.JSBUG("no support for multiple branches yet")
                branch = [branch.strip() for branch in branch.split(",")]
        elif isinstance(branch, (set, list)):
            raise self.exceptions.JSBUG("no support for multiple branches yet")
            branch = [branch.strip() for branch in branch]
        else:
            raise self.exceptions.JSBUG("branch should be a string or list, now %s" % branch)

        self.log("get code:%s:%s (%s)" % (url, path, branch))
        if self.myenv.config["SSH_AGENT"]:
            url = "git@github.com:%s/%s.git"
        else:
            url = "https://github.com/%s/%s.git"

        repo_url = url % (account, repo)
        fallback_url = "https://github.com/%s/%s.git" % (account, repo)
        exists, foundgit, dontpull, ACCOUNT_DIR, REPO_DIR = self._code_location_get(account=account, repo=repo)

        # if exists and reset and not pull:
        #     # need to remove because could be left over from previous sync operations
        #     # only reset if no pull
        #     self.delete(REPO_DIR)

        args = {}
        args["ACCOUNT_DIR"] = ACCOUNT_DIR
        args["REPO_DIR"] = REPO_DIR
        args["URL"] = repo_url
        args["FALLBACK_URL"] = fallback_url
        args["NAME"] = repo

        args["BRANCH"] = branch  # TODO:no support for multiple branches yet

        if "GITPULL" in os.environ:
            pull = str(os.environ["GITPULL"]) == "1"

        git_on_system = self.cmd_installed("git")

        if exists and not foundgit and not pull:
            """means code is already there, maybe synced?"""
            return gitpath

        if git_on_system and self.myenv.config["USEGIT"]:
            # there is ssh-key loaded
            # or there is a dir with .git inside and exists
            # or it does not exist yet
            # then we need to use git

            C = ""

            if exists is False:
                try:
                    C = """
                    set -e
                    mkdir -p {ACCOUNT_DIR}
                    """
                    self.log("get code [git] (first time): %s" % repo)
                    self.execute(C, args=args, showout=True, die_if_args_left=True)
                    C = """
                    cd {ACCOUNT_DIR}
                    git clone {URL} -b {BRANCH}
                    cd {NAME}
                    """
                    rc, out, err = self.execute(
                        C,
                        args=args,
                        die=True,
                        showout=True,
                        interactive=True,
                        retry=4,
                        errormsg="Could not clone %s" % repo_url,
                        die_if_args_left=True,
                    )
                except Exception:
                    C = """
                    set -e
                    mkdir -p {ACCOUNT_DIR}
                    """
                    self.log("get code [https] (second time): %s" % repo)
                    self.execute(C, args=args, showout=True, die_if_args_left=True)
                    C = """
                    cd {ACCOUNT_DIR}
                    git clone {FALLBACK_URL} -b {BRANCH}
                    cd {NAME}
                    """
                    rc, out, err = self.execute(
                        C,
                        args=args,
                        die=True,
                        showout=True,
                        interactive=True,
                        retry=4,
                        errormsg="Could not clone %s" % repo_url,
                        die_if_args_left=True,
                    )

            else:
                if pull:
                    if reset:
                        C = """
                        cd {REPO_DIR}
                        git checkout . --force
                        """
                        self.log("get code & ignore changes: %s" % repo)
                        self.execute(
                            C,
                            args=args,
                            retry=1,
                            errormsg="Could not checkout %s" % repo_url,
                            die_if_args_left=True,
                            interactive=True,
                        )
                    else:
                        if self.code_changed(REPO_DIR):
                            if self.ask_yes_no("\n**: found changes in repo '%s', do you want to commit?" % repo):
                                if "GITMESSAGE" in os.environ:
                                    args["MESSAGE"] = os.environ["GITMESSAGE"]
                                else:
                                    args["MESSAGE"] = input("\nprovide commit message: ")
                                    assert args["MESSAGE"].strip() != ""
                            else:
                                raise self.exceptions.Input("found changes, do not want to commit")
                            C = """
                            cd {REPO_DIR}
                            git add . -A
                            git commit -m "{MESSAGE}"
                            """
                            self.log("get code & commit [git]: %s" % repo)
                            self.execute(C, args=args, die_if_args_left=True, interactive=True)
                    C = """
                    cd {REPO_DIR}
                    git pull
                    """
                    self.log("pull code: %s" % repo)
                    self.execute(
                        C,
                        args=args,
                        retry=4,
                        errormsg="Could not pull %s" % repo_url,
                        die_if_args_left=True,
                        interactive=True,
                    )

                    if not checkoutbranch(args, branch):
                        raise self.exceptions.Input("Could not checkout branch:%s on %s" % (branch, args["REPO_DIR"]))

        else:
            self.log("get code [zip]: %s" % repo)
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
            self.execute(script, args=args, retry=3, errormsg="Cannot download:%s" % args["URL"], die_if_args_left=True)
            statinfo = os.stat("/tmp/jumpscale/download.zip")
            if statinfo.st_size < 100000:
                raise self.exceptions.Operations("cannot download:%s resulting file was too small" % args["URL"])
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
                    self.execute(script, args=args, die=True, die_if_args_left=True, interactive=True)
                except Exception as e:
                    self.shell()

        return gitpath

    def config_load(self, path="", if_not_exist_create=False, executor=None, content="", keys_lower=False):
        """
        only 1 level deep toml format only for int,string,bool
        no multiline support for text fields

        :param: keys_lower if True will lower the keys

        return dict

        """
        path = self.text_replace(path)
        res = {}
        if content == "":
            if executor is None:
                if os.path.exists(path):
                    t = self.file_text_read(path)
                else:
                    if if_not_exist_create:
                        self.config_save(path, {})
                    return {}
            else:
                if executor.exists(path):
                    t = executor.file_read(path)
                else:
                    if if_not_exist_create:
                        self.config_save(path, {}, executor=executor)
                    return {}
        else:
            t = content

        for line in t.split("\n"):
            if line.strip() == "":
                continue
            if line.startswith("#"):
                continue
            if "=" not in line:
                raise self.exceptions.Input("Cannot process config: did not find = in line '%s'" % line)
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

    def config_save(self, path, data, upper=True, executor=None):
        path = self.text_replace(path)
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
            self.file_write(path, out)
