import os
import subprocess
import errno
from Jumpscale import j

PIPE = subprocess.PIPE

j.core.platformtype


if j.core.platformtype.myplatform.platform_is_windows:
    from win32file import ReadFile, WriteFile
    from win32pipe import PeekNamedPipe
    import msvcrt
else:
    import select
    import fcntl


if j.core.platformtype.myplatform.platform_is_linux:
    try:
        from pexpect import pxssh
    except ImportError as e:
        # We want this to go to stderr, otherwise applications relying on stdout
        # output (build command generator scripts) are pretty busted.
        print("cannot find pxssh")
        pass

if j.core.platformtype.myplatform.platform_is_unix:
    try:
        import pexpect
    except ImportError as e:
        print("did not find pexpect")
        j.core.platformtype.myplatform.platform_is_linux
        try:
            j.sal.ubuntu.apt_install("python-pexpect")
        except BaseException:
            pass

JSBASE = j.baseclasses.object


class Popen(subprocess.Popen, JSBASE):
    def __init__(self):
        JSBASE.__init__(self)

    def recv(self, maxsize=None):
        return self._recv("stdout", maxsize)

    def recv_err(self, maxsize=None):
        return self._recv("stderr", maxsize)

    def send_recv(self, input="", maxsize=None):
        return self.send(input), self.recv(maxsize), self.recv_err(maxsize)

    def get_conn_maxsize(self, which, maxsize):
        if maxsize is None:
            maxsize = 1024
        elif maxsize < 1:
            maxsize = 1
        return getattr(self, which), maxsize

    def _close(self, which):
        getattr(self, which).close()
        setattr(self, which, None)

    if j.core.platformtype.myplatform.platform_is_windows:

        def send(self, input):
            if not self.stdin:
                return None
            try:
                x = msvcrt.get_osfhandle(self.stdin.fileno())
                (errCode, written) = WriteFile(x, input)
            except ValueError:
                self._log_debug("close stdin")
                return self._close("stdin")
            except (subprocess.pywintypes.error, Exception) as why:
                if why[0] in (109, errno.ESHUTDOWN):
                    self._log_debug("close stdin")
                    return self._close("stdin")
                raise
            return written

        def _recv(self, which, maxsize):
            conn, maxsize = self.get_conn_maxsize(which, maxsize)
            if conn is None:
                return None

            try:
                x = msvcrt.get_osfhandle(conn.fileno())
                (read, nAvail, nMessage) = PeekNamedPipe(x, 0)
                if maxsize < nAvail:
                    nAvail = maxsize
                if nAvail > 0:
                    (errCode, read) = ReadFile(x, nAvail, None)
            except ValueError:
                return self._close(which)
            except (subprocess.pywintypes.error, Exception) as why:
                if why[0] in (109, errno.ESHUTDOWN):
                    return self._close(which)
                raise

            if self.universal_newlines:
                read = self._translate_newlines(read)
            return read

    else:

        def send(self, input):
            if not self.stdin:
                return None

            if not select.select([], [self.stdin], [], 0)[1]:
                return 0

            try:
                written = os.write(self.stdin.fileno(), input)
            except OSError as why:
                if why[0] == errno.EPIPE:  # broken pipe
                    self._log_error("close stdin")
                    return self._close("stdin")
                raise

            return written

        def _recv(self, which, maxsize):
            conn, maxsize = self.get_conn_maxsize(which, maxsize)
            if conn is None:
                return None

            flags = fcntl.fcntl(conn, fcntl.F_GETFL)
            if not conn.closed:
                fcntl.fcntl(conn, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            try:
                if not select.select([conn], [], [], 0)[0]:
                    return ""

                r = conn.read(maxsize)
                if not r:
                    return self._close(which)

                if self.universal_newlines:
                    r = self._translate_newlines(r)
                return r
            finally:
                if not conn.closed:
                    fcntl.fcntl(conn, fcntl.F_SETFL, flags)


class ExpectTool(j.baseclasses.object):
    __jslocation__ = "j.tools.expect"

    @staticmethod
    def new(cmd=None):
        """Create a new Expect session

        @param cmd: Command to execute
        @type cmd: string

        @returns: Expect session
        @rtype cmdline.Expect.Expect
        """
        return Expect(cmd=cmd or "")


class Expect(j.baseclasses.object):
    _p = None  # popen process
    error = False
    _lastsend = ""
    _ignoreStdError = False
    _ignoreLineFilter = []
    _lastOutput = ""  # stdOut from last send
    _lastError = ""  # stdError from last send
    _cleanStringEnabled = True  # if True every output will be cleaned from ansi codes
    _timeout = False  # if true a send&wait statement has timed out
    _waitTokens = []  # list of tokens where we wait on when executing

    def __init__(self, cmd=""):
        JSBASE.__init__(self)
        PIPE = subprocess.PIPE
        self._prompt = ""

        if not cmd:
            if cmd == "" and j.core.platformtype.myplatform.platform_is_windows:
                cmd = "cmd"
            if cmd == "" and not j.core.platformtype.myplatform.platform_is_windows:
                cmd = "sh"
                self._pxssh = pxssh.pxssh()
            self._p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)

        elif cmd and cmd != "ssh" and not j.core.platformtype.myplatform.platform_is_windows:
            self.pexpect = pexpect.spawn(cmd)
            if cmd == "sh":
                self.expect("#")
                self.setPrompt()
                self.prompt()

        self.enableCleanString()

    def log(self, message, category="", level=5):
        category = "expect.%s" % category
        category = category.strip(".")
        self._log_debug(message, category=category, level=level)

    def enableCleanString(self):
        """
        All output will be cleaned from ANSI code and other unwanted garbage
        """
        self._cleanStringEnabled = True

    def disableCleanString(self):
        """
        Disable output cleaning, e.g. stripping ANSI code
        """
        self._cleanStringEnabled = False

    def _add2lastOutput(self, str):
        self._lastOutput = self._lastOutput + str

    def _add2lastError(self, str):
        self._lastError = self._lastError + str

    def setIgnoreStdError(self):
        """
        Disable display of stderr error messages to the standard output
        """
        self._ignoreStdError = True

    def unsetIgnoreStdError(self):
        """
        Enable display error output (stderr)
        """
        self._ignoreStdError = False

    def addIgnoreLineFilter(self, filter):
        """
        Add a filter on output lines. Lines matching the provided filter will not be displayed on stdout or stderr.
        """
        self._ignoreLineFilter.append(filter)

    def addWaitToken(self, token):
        """
        Adds a token that we will wait for when using C{self.wait()}
        """
        self._waitTokens.append(token)

    def resetWaitTokens(self, token):
        """
        Remove all tokens we'd wait for in self.wait()
        """
        self._waitTokens = []

    def clearReceive(self):
        self._lastOutput = ""
        self._lastError = ""

    def login(self, remote, passwd, seedpasswd, initial=False, timeout=10):
        # login over ssh
        self.send("ssh root@%s" % remote)
        if initial:
            result = self.expect("continue connecting", timeout=2)
            self.send("yes\n")

        result = self.expect("password:", timeout=timeout)

        if result == "E":
            self._log_debug("did not see passwd")
            result = self.expect("continue connecting", timeout=timeout / 2)

            if result == 0:
                self._log_debug("saw confirmation ssh key")
                self._log_debug("send yes for ssh key")
                self.send("yes\n")
                result = self.expect("password:", timeout=timeout / 2)
            else:
                raise j.exceptions.RuntimeError(
                    "Could not login with std passwd nor with seedpasswd, did not get passwd str"
                )

        if result != "E":
            # we saw passwd
            self.send(passwd)
            result = self.expect("#", timeout=timeout / 2)
            if result == "E":
                result = self.expect("Permission denied")
                if result != "E" and seedpasswd != "":
                    self._log_debug("permission denied, will try to use seedpasswd")
                    self.send(seedpasswd)
                    result = self.expect("#")
                    if result == "E":
                        raise j.exceptions.RuntimeError("could not login with std passwd nor with seedpasswd")
                    self._log_debug("seedpasswd worked")

                    self._log_debug("change passwd")
                    self.send("passwd")
                    result = self.expect("password:")
                    if result == "E":
                        raise j.exceptions.RuntimeError("did not get passwd prompt.")
                    self.send(passwd)
                    result = self.expect("password:")
                    if result == "E":
                        raise j.exceptions.RuntimeError("did not get passwd prompt.")
                    self.send(passwd)
                    result = self.expect("#")
                    if result == "E":
                        raise j.exceptions.RuntimeError("could not change passwd")
                    return
                else:
                    raise j.exceptions.RuntimeError("Could not login did not see permission denied.")
            else:
                return

        if result != "E":
            # we saw passwd
            self.send(passwd)
            result = self.expect("#")
            if result == "E":
                raise j.exceptions.RuntimeError("could not login")
            return
        else:
            # did not see passwd again
            raise j.exceptions.RuntimeError("Did not see passwd request, could not login")

        return

    # def login(self, ip, login, password, login_timeout=15):
    #     """Log the user into the given server

    #     By default the prompt is rather optimistic and should be considered more of
    #     an example. It is better to try to match the prompt as exactly as possible to prevent
    #     any false matches by server strings such as a "Message Of The Day" or something.

    #     The closer you can make the original_prompt match your real prompt the better.
    #     A timeout causes not necessarily the login to fail.

    #     In case of a time out we assume that the prompt was so weird that we could not match
    #     it. We still try to reset the prompt to something more unique.

    #     If that still fails then we return False.
    #     """
    #     if not j.core.platformtype.myplatform.platform_is_linux:
    #         raise j.exceptions.RuntimeError('pexpect/pxssh not supported on this platform')

    #     if not self._pxssh.login(ip, login, password, login_timeout=login_timeout):
    #         raise j.exceptions.Value('Could not connect to %s, check either login/password are not correct or host is not reacheable over SSH.'%ip)
    #     else:
    #         self._log_debug('SSH %s@%s session login successful' % (login, ip), 6)

    def logout(self):
        """This sends exit. If there are stopped jobs then this sends exit twice.
        """
        self.send("logout")

    def receive(self):
        """
        Receive standard out, stderror if available
        return stdout,stderror
        """

        if j.core.platformtype.myplatform.platform_is_windows:
            out = self.receiveOut()
            err = self.receiveError()
            return out, err

        elif j.core.platformtype.myplatform.isunix and self.pexpect:

            if self.pexpect.match:
                # out='%s%s'%(self.pexpect.after, self.pexpect.buffer)
                out = self.pexpect.before
                out = self._cleanStr(out)
                return out, ""
            else:
                before = self.pexpect.before
                before = self._cleanStr(before)
                return str(before), ""

        elif j.core.platformtype.myplatform.platform_is_linux and not self.pexpect:

            return str(self._pxssh).before, ""

        o.errorhandler.raiseBug(message="should never come here, unsupported platform", category="expect.receive")

    def receivePrint(self):
        """
        Receive data from stdout and stderr and displays them
        This function also remembers this information for later usage in the
        classes C{_out} & C{_error}.
        """
        out, err = self.receive()
        self._log_debug(out)
        if err != "":
            self._log_error("ERROR:")
            self._log_error(err)

    def _receiveOut(self):  # windows only
        """
        Receive standard out and return. This information is stored for later usage
        in the class C{_out}.
        """
        out = self._receive(False)
        if self._cleanStringEnabled:
            out = self._cleanStr(out)
        self._add2lastOutput(out)
        self._log_debug("stdout:%s" % out, 9)
        return out

        # TODO: P2 not right,can never work, needs to check if expect or popen or, ...

    def _receiveError(self):  # windows only
        """
        Receive standard error and return. This information is stored for later usage
        in the class C{_error}.
        """
        err = self._receive(True)
        if self._cleanStringEnabled:
            err = self._cleanStr(err)
        self._add2lastError(err)
        return err

        # TODO: P2 not right,can never work, needs to check if expect or popen or, ...

    def pprint(self):
        """
        Print the result of all send & receive operations till now on local C{stdout}.
        """
        out = self._ignoreLinesBasedOnFilter(self._lastOutput)
        error = self._lastError
        if error != "":
            j.tools.console.echo("%s/nerror:%s" % (out, error))
        else:
            j.tools.console.echo(out)

    # def _receive(self,checkError=False):
    #     #stdin=self._stdin
    #     #stdout=self._stdout
    #     t=.1
    #     e=1
    #     tr=5
    #     p=self._p
    #     if tr < 1:
    #         tr = 1
    #     x = time.time()+t
    #     y = []
    #     r = ''
    #     pr = p.recv
    #     #check error
    #     if checkError:
    #         pr = p.recv_err
    #     while time.time() < x or r:
    #         r = pr()
    #         if r is None:
    #             if e:
    #                 raise Exception("Exception occured")
    #             else:
    #                 break
    #         elif r:
    #             y.append(r)
    #         else:
    #             time.sleep(max((x-time.time())/tr, 0))
    #     returnval=''.join(y)
    #     returnval=returnval.replace("\\n","\n")
    #     returnval=returnval.replace("\\r","\r")
    #     returnval=self._cleanStr(returnval)
    #     if returnval != "" and checkError:
    #         self.error=True
    #     return returnval

    def _cleanStr(self, s):
        """
        Remove most ANSI characters (screen emulation).
        Remove double prompts (if used e.g. with remote ssh).
        """
        state = "start"
        # s=s.encode('ascii')
        strclean = ""
        # s=s.replace(unichr(27)+"]0;","")
        s = self._strRemovePromptSSHAnsi(s)
        for item in s:
            if self._ansiCheckStart(item):
                state = "ignore"
                teller = 0
            if state != "ignore":
                strclean = strclean + item
            if state == "ignore" and self._ansiCheckStop(item):
                state = "ok"
        strclean = strclean.replace(chr(27) + chr(7), "")
        strclean = strclean.replace(chr(27) + chr(8), "")
        strclean = strclean.replace(chr(7), "")
        return strclean

    def _strRemovePromptSSHAnsi(self, s):
        state = "start"
        strclean = ""
        for t in range(0, len(s)):
            if t + 3 < len(s):
                find = s[t] + s[t + 1] + s[t + 2] + s[t + 3]
            else:
                find = ""
            if find == chr(27) + "]0;":
                # found prompt
                state = "ignore"
            if state != "ignore":
                strclean = strclean + s[t]
            if state == "ignore" and s[t] == chr(7):
                state = "ok"
        return strclean

    def _ansiCheckStart(self, s):
        pattern = [27]
        found = False
        for item in pattern:
            if ord(s) == item:
                found = True
        return found

    def _ansiCheckStop(self, s):
        pattern = "cnRhlL()HABCDfsurMHgKJipm"
        found = False
        for item in pattern:
            if ord(s) == ord(item):
                found = True
        return found

    def send(self, data="", newline=True):
        """
        Send a command to shell.
        After sending a command, one of the receive functions must be called to
        check for the result on C{stdout} or C{stderr}.
        """
        self._log_info("send: %s" % data, category="send")
        self._lastsend = data
        self._lastOutput = ""
        self._lastError = ""

        if j.core.platformtype.myplatform.isunix:
            if self.pexpect:
                if newline:
                    data = data.rstrip("\n")
                    return self.pexpect.sendline(data)
                else:
                    return self.pexpect.send(data)

        if j.core.platformtype.myplatform.platform_is_windows:
            data = data + "\r\n"

        p = self._p

        if len(data) != 0:
            if j.core.platformtype.myplatform.platform_is_windows:
                sent = p.send(data)
                if sent is None:
                    raise Exception("ERROR: Data sent is none")
                data = buffer(data, sent)
            elif j.core.platformtype.myplatform.platform_is_linux:
                self._pxssh.sendline(data)

    # def read(self):
    #     o=self.pexpect.read_nonblocking()
    #     out=""
    #     while o != "":
    #         print o,
    #         o=self.pexpect.read_nonblocking()
    #         out+=o
    #     return out

    def setPrompt(self, prompt="#.#.#"):
        self.send("PS1='%s'" % prompt)
        self._prompt = prompt
        self.prompt()

    def executeSequence(self, sequence, cmd):
        """
        sequence=[[regex1,tosend,stepname,timeout],...]
        timeout is optional, also stepname is optional
        at end it waits for prompt
        """
        self.send(cmd)
        out = ""
        m = len(sequence)
        nr = 0
        for item in sequence:
            nr += 1
            if len(item) == 2:
                regex = item[0]
                tosend = item[1]
                stepname = nr
                timeout = 10
            elif len(item) == 3:
                regex = item[0]
                tosend = item[1]
                stepname = item[2]
                timeout = 10
            elif len(item) == 4:
                regex = item[0]
                tosend = item[1]
                stepname = item[2]
                timeout = item[3]
            else:
                raise j.exceptions.RuntimeError("Error in syntax sequence,\n%s" % sequence)

            result = self.expect([regex, self._prompt], timeout=timeout)
            if result == 0 or nr == m:
                o = self.receive()[0]
                o += "\nSTEP: %s: %s\n%s\n" % (nr, stepname, o)
                out += "%s\n" % o
                self._log_debug(o)
                self.send(tosend, False)

            elif result is False:
                raise j.exceptions.RuntimeError("Timeout in execution of sequence.\nError:\n%s" % o)
            else:
                raise j.exceptions.RuntimeError("Error in execution of sequence.\nError:\n%s" % o)
        return self.prompt()

    def prompt(self, timeout=5):
        """Expect the prompt.

        Return C{True} if the prompt was matched.
        Returns C{False} if there was a time out.
        """
        self.expect(self._prompt, timeout=timeout)

    def _removeFirstLine(self, text):
        lines = text.splitlines()
        linenr = 0
        cleanstr = ""
        for line in lines:
            linenr = linenr + 1
            if linenr != 1:
                cleanstr = cleanstr + line + "\n"
        return cleanstr

    def execShellCmd(self, cmd, timeout=30):
        """
        execute a command and wait on the prompt
        """
        self.send(cmd)
        self.prompt(timeout=timeout)
        out, err = self.receive()
        return out

    def do(self, data, timeout=30):
        """
        This function is a combination of the functions C{send}, C{receive} and C{print}.

        The first line is also removed (this is the echo from what has been sent).
        Use this if you quickly want to execute something from the command line.
        """
        self.send(data)
        self.wait(timeout)
        self._lastOutput = self._removeFirstLine(self._lastOutput)
        self.pprint()

    # def waitTillEnd(self):
    #    """
    #    TODO: not clear what it does anw why needed
    #    """
    #    self._p.wait()

    def _checkForTokens(self, text):
        if text == "":
            return 0
        text = text.lower()
        tokens = self._waitTokens
        tokennr = 0
        for token in tokens:
            # self._log_debug("checktoken %s : %s" % (token,text))
            tokennr = tokennr + 1
            token = token.lower()
            if text.find(token) != -1:
                # token found
                self._log_debug("Found token:%s" % token, 9)
                return tokennr
        return 0

    def _ignoreLinesBasedOnFilter(self, str):
        lines = str.splitlines()
        returnstr = ""
        for line in lines:
            foundmatch = False
            for filter in self._ignoreLineFilter:
                if line.find(filter) != -1:
                    self._log_debug("Found ignore line:%s:%s" % (filter, line), 9)
                    foundmatch = True
            if foundmatch is False:
                returnstr = returnstr + line + "\n"
        return returnstr

    def wait(self, timeoutval=30):
        """
        Wait until we detect tokens (see L{addWaitToken})

        @param timeoutval: time in seconds we maximum will wait
        """
        self._log_info("wait: %s sec" % timeoutval, category="wait")
        timeout = False
        starttime = j.data.time.getTimeEpoch()
        r = ""  # full return
        returnpart = ""  # one time return after receive
        done = False  # status param
        tokenfound = 0
        self._timeout = False
        while timeout is False and done is False:
            returnpart, err = self.receive()
            self._log_debug(returnpart)
            tokenfound = self._checkForTokens(returnpart)
            # self._log_debug("tokenfound:%s"%tokenfound)
            returnpart = self._ignoreLinesBasedOnFilter(returnpart)
            r = r + returnpart
            curtime = j.data.time.getTimeEpoch()
            self._log_debug("TimeoutCheck on waitreceive: %s %s %s" % (curtime, starttime, timeoutval), 8)
            if curtime - starttime > timeoutval:
                self._log_debug("WARNING: execute %s timed out (timeout was %s)" % (self._lastsend, timeoutval), 6)
                timeout = True
            if tokenfound > 0:
                done = True
        out, err = self.receive()
        r = r + out
        if timeout:
            r = ""
            self._timeout = True
        return tokenfound, r, timeout

    def expect(self, outputToExpect, timeout=2):
        """
        Pexpect expect method wrapper
        usage: Excuting a command that expects user input, this method can be used to
        expect the question asked then send the answer
        Example:
        Expect = j.tools.expect.new('passwd')
        if Expect.expect('Enter new'):
            Expect.send('newPasswd')

            if Expect.expect('Retype new'):
                Expect.send('anotherPasswd')

                if Expect.expect('passwords do not match'):
                    j.tools.console.echo(Expect.receive())
        else:
            j.tools.console.echo(Expect.receive())

        @return 'E' when error

        """
        self._log_debug("Expect %s " % outputToExpect, 7)

        try:
            result = self.pexpect.expect(outputToExpect, timeout=timeout)
            return result
        except BaseException:
            msg = 'Failed to expect "%s", found "%s" instead' % (outputToExpect, self.receive())
            # print msg
            self._log_debug(msg, 7)
        return "E"
