import sys
import os
import getpass
import grp
import traceback
import pudb

from SSHAgent import SSHAgent
from Tools import Tools
from RedisTools import RedisTools
from LogHandler import LogHandler
from BaseInstaller import BaseInstaller
from OSXInstaller import OSXInstaller
from UbuntuInstaller import UbuntuInstaller
from JumpscaleInstaller import JumpscaleInstaller
from DockerFactory import DockerFactory

DEFAULT_BRANCH = "unstable"
DEFAULT_BRANCH_WEB = "development"
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

GITREPOS["tutorials"] = [
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


class Installers:
    pass


class MyEnv:
    def __init__(self):
        """

        :param configdir: default /sandbox/cfg, then ~/sandbox/cfg if not exists
        :return:
        """
        self.tools = Tools(self)
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

        self.GITREPOS = GITREPOS
        self._db = None

        self.installers = Installers()
        self.installers.osx = OSXInstaller(self)
        self.installers.ubuntu = UbuntuInstaller(self)
        self.installers.base = BaseInstaller(self)
        self.installers.jumpscale = JumpscaleInstaller(self)

        self.docker = DockerFactory(self)
        self.redis = RedisTools(self)

        if self.platform() == "linux":
            self.platform_is_linux = True
            self.platform_is_unix = True
            self.platform_is_osx = False
        elif "darwin" in self.platform():
            self.platform_is_linux = False
            self.platform_is_unix = True
            self.platform_is_osx = True
        elif "win32" in self.platform():
            self.platform_is_linux = False
            self.platform_is_unix = False
            self.platform_is_osx = False
            self.platform_is_windows = True
        else:
            raise self.tools.exceptions.Base("platform not supported, only linux or osx and windows for now.")

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
            self.tools.execute(script, interactive=True, args=args, die_if_args_left=True)

        # Set codedir
        self.tools.dir_ensure(f"{basedir}/code")
        self.config_file_path = os.path.join(configdir, "jumpscale_config.toml")
        self.state_file_path = os.path.join(configdir, "jumpscale_done.toml")

        if self.tools.exists(self.config_file_path):
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

        self.sshagent = SSHAgent(myenv=self)

        sys.excepthook = self.excepthook
        if self.tools.exists("{}/bin".format(self.config["DIR_BASE"])):  # To check that Js is on host
            self.loghandler_redis = LogHandler(self, db=self.db)
        else:
            # print("- redis loghandler cannot be loaded")
            self.loghandler_redis = None

        self.__init = True

    @property
    def db(self):
        if self._db == "NOTUSED":
            return None
        if not self._db:
            if self.redis.client_core_get(die=False):
                self._db = self.redis._core_get()
            else:
                self._db = "NOTUSED"
        return self._db

    def redis_start(self):
        self._db = self.redis._core_get()

    def secret_set(self, secret=None, secret_expiration_hours=48):
        """
        can be the hash or the originating secret passphrase

        """
        if not secret:
            secret = self.tools.ask_password("please specify secret passphrase for your SDK/3bot (<32chars)")
            assert len(secret) < 32

        secret = self._secret_format(secret)

        expiration = secret_expiration_hours * 3600

        if self.db:
            self.db.set("threebot.secret.encrypted", secret, ex=expiration)

        return secret

    def _secret_format(self, secret):

        if not isinstance(secret, bytes):
            secret = secret.encode()

        if len(secret) != 32:
            import hashlib

            m = hashlib.md5()
            m.update(secret)

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
            #         self.secret_set(secret=secret)
            #         toremove = key
            #
            # if toremove:
            #     # means we can remove the --secret from sys.arg
            #     # important to do or future command line arg parsing will fail
            #     sys.argv.pop(sys.argv.index(toremove))

            if self.db:
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
            self.installers.ubuntu.ensure_version()
        elif "darwin" not in platform:
            raise self.tools.exceptions.Base("Your platform is not supported")

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
            # config["DIR_CODE"] = "%s/code" % config["DIR_BASE"]
            # if self.tools.exists("%s/code" % config["DIR_BASE"]):
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
        if not self.loghandlers != []:
            self.tools.shell()

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
        if isinstance(exception_obj, self.tools.exceptions.RemoteException):
            print(self.tools.text_replace("{RED}*****Remote Exception*****{RESET}"))
            logdict = exception_obj.data
            self.tools.log2stdout(logdict)

            exception_obj.data = None
            exception_obj.exception = None
        # logdict = self.tools.log(tb=tb, level=level, exception=exception_obj, stdout=stdout)
        try:
            logdict = self.tools.log(tb=tb, level=level, exception=exception_obj, stdout=stdout)
        except Exception as e:
            self.tools.pprint("{RED}ERROR IN LOG HANDLER")
            print(e)
            ttype, msg, tb = sys.exc_info()
            traceback.print_exception(etype=ttype, tb=tb, value=msg)
            self.tools.pprint("{RESET}")
            raise e
            sys.exit(1)

        exception_obj._logdict = logdict

        if self.debug and tb:
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
        self.tools.file_edit(self.config_file_path)

    def _config_load(self):
        """
        loads the configuration file which default is in {DIR_BASE}/cfg/jumpscale_config.toml
        {DIR_BASE} normally is /sandbox
        """
        config = self.tools.config_load(self.config_file_path)
        self.config = self.config_default_get(config)

    def config_save(self):
        self.tools.config_save(self.config_file_path, self.config)

    def _state_load(self):
        """
        only 1 level deep toml format only for int,string,bool
        no multiline
        """
        if self.tools.exists(self.state_file_path):
            self.state = self.tools.config_load(self.state_file_path, if_not_exist_create=False)
        elif not self.readonly:
            self.state = self.tools.config_load(self.state_file_path, if_not_exist_create=True)
        else:
            self.state = {}

    def state_save(self):
        if self.readonly:
            return
        self.tools.config_save(self.state_file_path, self.state)

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
        self.tools.delete(self.state_file_path)
        self._state_load()
