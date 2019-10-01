from Jumpscale import j
from Jumpscale.tools.bash.Profile import Profile
from functools import wraps
import inspect
import os

from .JSBase import JSBase


class builder_method:
    """A Decorator to be used in all builder methods
    this will provide:
    1- State check to make sure not to do one action multiple times
    2- Making sure that actions are done in the correct order, for instance it will make sure that build is done before
       installation
    """

    def __init__(self, **kwargs_):
        if "log" in kwargs_:
            self.log = j.data.types.bool.clean(kwargs_["log"])
        else:
            self.log = True
        if "done_check" in kwargs_:
            self.done_check = j.data.types.bool.clean(kwargs_["done_check"])
        else:
            self.done_check = True

    @staticmethod
    def get_default_zhub_client(kwargs):
        """Gets the zhub client to be used to upload the flist
        this will depend on two parameters (zhub_client and flist_create)
        - if zerohub instance provided it will be used
        - if no zhub instance but flist_create = True will try to use the main zhub instance
        :param kwargs: kwargs passed to the builder method
        :return: zhub_client to be used
        :raises: RuntimeError if no zhub instance provided and the main instance is not configured
        """
        # only use "main" client, because should be generic usable
        zhub_client = kwargs.get("zhub_client")
        if not zhub_client and kwargs.get("flist_create"):
            if not j.clients.zhub.exists(name="main"):
                raise j.exceptions.Base("Cannot find main zhub client, please configure main instance")

            # verifying the client
            zhub_client = j.clients.zhub.get(name="main")
            zhub_client.list(username=zhub_client.username)
        return zhub_client

    @staticmethod
    def get_argument_names(func):
        """Gets the args of a function ordered

        :param func: a method to get parameters from
        :return: list of args names
        """
        argspec = inspect.getargspec(func)
        args = argspec.args
        if argspec.varargs:
            args += argspec.varargs
        if argspec.keywords:
            args += argspec.keywords
        return args

    def get_all_as_keyword_arguments(self, func, args, kwargs):
        """Converts all passed parameters to dict
        we needed this because we need a unified way to deal with the parameters passed to the method
        :param func: a function to get the arguments data from
        :param args: the passed args
        :param kwargs: the passed kwargs
        :return: dict of args and kwargs as if it was all kwargs
        """
        arg_names = self.get_argument_names(func)
        if "self" in arg_names:
            arg_names.remove("self")

        if not arg_names:
            return kwargs

        arg_names = arg_names[: len(args)]
        kwargs.update(dict(zip(arg_names, args)))

        signature = inspect.signature(func)
        for _, param in signature.parameters.items():
            if param.name not in kwargs:
                if not isinstance(param.default, inspect._empty):
                    kwargs[param.name] = param.default

        return kwargs

    def apply_method(self, func, kwargs):
        arg_names = self.get_argument_names(func)
        kwargs = {key: value for key, value in kwargs.items() if key in arg_names}
        return func(**kwargs)

    def already_done(self, func, builder, key, reset):
        """ Check if this method was already done or not

        *Note* if you pass reset=True to any method it will be executed again
        :param func: the function called
        :param builder: the builder used
        :param kwargs: kwargs passed to the method (use get_all_as_keyword_arguments to get anything passed to the
        method as kwargs)
        :return: True means it was already done and you don't need to redo, False means not done before or reset=True
        """

        reset = j.data.types.bool.clean(reset)
        if reset is True:
            builder._done_reset()  # removes all states from this specific builder
            builder.reset()
            return False
        if self.done_check and builder._done_check(key, reset):
            return True
        else:
            return False

    def __call__(self, func):
        @wraps(func)
        def wrapper_action(builder, *args, **kwargs):
            """The main wrapper method for the decorator, it will do:
            1- check if the method is going to be executed or it's already done before
            2- make sure that the previous method were executed in the correct order
            3- choose the correct env file for the action
            4- prepare any needed parameters AKA zerohub client in case of creating a flist
            :param builder: the builder self
            :param args: args passed to the method
            :param kwargs: kwargs passed to the method
            :return: if the method was already done it will return BuilderBase.ALREADY_DONE_VALUE
            """
            name = func.__name__

            if not j.application._log2fs_session_name:
                j.application.log2fs_register(builder._classname)
            j.application.log2fs_context_change(name)

            kwargs = self.get_all_as_keyword_arguments(func, args, kwargs)
            kwargs_without_reset = {key: value for key, value in kwargs.items() if key not in ["reset", "self"]}
            done_key = name + "_" + j.data.hash.md5_string(str(kwargs_without_reset))
            reset = kwargs.get("reset", False)
            state_reset = kwargs.get("state_reset", False)

            reset = reset or state_reset

            # if reset:
            #     builder.state_reset()  # lets not reset the full module

            if self.already_done(func, builder, done_key, reset):
                builder._log_info("no need to do: %s:%s, was already done" % (builder._classname, kwargs_without_reset))
                return builder.ALREADY_DONE_VALUE

            # Make sure to call _init before any method
            if name is not "_init":
                builder._init()

            if name == "build":
                if builder._done_check(done_key):
                    builder.stop()
                builder.profile_builder_select()

            if name == "install":
                if builder._done_check(done_key):
                    builder.stop()
                builder.profile_builder_select()
                builder.build()

            if name == "sandbox":
                builder.profile_builder_select()
                builder.install()
                kwargs["zhub_client"] = self.get_default_zhub_client(kwargs)

            if name in ["stop", "running", "_init"]:
                builder.profile_sandbox_select()
                self.done_check = False

            if self.log:
                builder._log_debug("action:%s() start" % name)

            kwargs["self"] = builder
            res = self.apply_method(func, kwargs)

            if name == "sandbox" and kwargs.get("flist_create", False):
                res = builder._flist_create(kwargs["zhub_client"], kwargs.get("merge_base_flist"))

            builder._done_set(done_key)

            if self.log:
                builder._log_debug("action:%s() done -> %s" % (name, res))

            return res

        return wrapper_action


class BuilderBaseClass(JSBase):
    """
    doc in /sandbox/code/github/threefoldtech/jumpscaleX_core/docs/Internals/builders/Builders.md
    """

    ALREADY_DONE_VALUE = "ALREADY DONE"

    def __init__(self):
        self._bash = None
        self._classname = self.__class__.__jslocation__.lower().split(".")[-1]
        self.DIR_BUILD = "/tmp/builders/{}".format(self._classname)
        self.DIR_SANDBOX = "/tmp/package/{}".format(self._classname)
        JSBase.__init__(self)

    def state_sandbox_set(self):
        """
        bring builde in sandbox state
        :return:
        """
        self.state = self.state.SANDBOX
        self._bash = None

    def profile_home_select(self):
        if self.profile.state == "home":
            return
        self._profile_home_set()

    def profile_home_set(self):
        pass

    def _profile_home_set(self):

        self._bash = j.tools.bash.get(self._replace("{DIR_HOME}"))
        self.profile.state = "home"

        self.profile_home_set()

        self._profile_defaults_system()

        self.profile.env_set("PS1", "HOME: ")

        self._log_info("home profile path in:%s" % self.profile.profile_path)

    def profile_builder_select(self):
        if self.profile.state == "builder":
            return
        self._profile_builder_set()

    def profile_builder_set(self):
        pass

    def _profile_defaults_system(self):

        self.profile.env_set("PYTHONHTTPSVERIFY", 0)

        self.profile.env_set("LC_ALL", "en_US.UTF-8")
        self.profile.env_set("LANG", "en_US.UTF-8")

    def _profile_builder_set(self):
        def _build_flags(env_name, delimiter):
            flags = self.profile.env_get(env_name).split(":")
            flags = ["-{}{}".format(delimiter, flag) for flag in flags]
            return '"{}"'.format(" ".join(flags))

        self._remove("{DIR_BUILD}/env.sh")
        self._bash = j.tools.bash.get(self._replace("{DIR_BUILD}"))

        self.profile.state = "builder"

        self.profile_builder_set()

        self.profile.env_set_part("LIBRARY_PATH", "/usr/lib")
        self.profile.env_set_part("LIBRARY_PATH", "/usr/local/lib")
        self.profile.env_set_part("LIBRARY_PATH", "/lib")
        self.profile.env_set_part("LIBRARY_PATH", "/lib/x86_64-linux-gnu")
        library_path = os.environ.get("LIBRARY_PATH") or ""
        self.profile.env_set_part("LIBRARY_PATH", library_path, end=True)

        self.profile.env_set("LD_LIBRARY_PATH", self.profile.env_get("LIBRARY_PATH"))  # makes copy

        lds = _build_flags("LIBRARY_PATH", "L")
        self.profile.env_set("LDFLAGS", lds)

        self.profile.env_set_part("CPPPATH", "/usr/include")
        self.profile.env_set("CPPPATH", self.profile.env_get("CPPPATH"))

        cps = _build_flags("CPPPATH", "I")
        self.profile.env_set("CPPFLAGS", cps)

        self.profile.env_set("PS1", "PYTHONBUILDENV: ")

        self._profile_defaults_system()

        self.profile.path_add(self._replace("{DIR_BUILD}/bin"))

        self._log_info("build profile path in:%s" % self.profile.profile_path)

    def profile_sandbox_select(self):
        if self.profile.state == "sandbox":
            return
        self._profile_sandbox_set()

    def profile_sandbox_set(self):
        pass

    def _profile_sandbox_set(self):

        self._bash = j.tools.bash.get("/sandbox")

        self.profile.state = "sandbox"

        # cannot manipuate env.sh in sandbox, should be set properly by design
        if self.profile.profile_path != "/sandbox/env.sh":
            self.profile.path_add("/sandbox/bin")

            self.profile.env_set("PYTHONHTTPSVERIFY", 0)

            self.profile.env_set_part("PYTHONPATH", "/sandbox/lib")
            self.profile.env_set_part("PYTHONPATH", "/sandbox/lib/jumpscale")

            self.profile.env_set("LC_ALL", "en_US.UTF-8")
            self.profile.env_set("LANG", "en_US.UTF-8")

            self.profile.path_delete("${PATH}")

            if j.core.platformtype.myplatform.platform_is_osx:
                self.profile.path_add("${PATH}", end=True)

            self.profile.env_set_part("PYTHONPATH", "$PYTHONPATH", end=True)

            self.profile_sandbox_set()

        self._log_info("sandbox profile path in:%s" % self.profile.profile_path)

    @property
    def bash(self):
        if not self._bash:
            self._bash = j.tools.bash.sandbox
        return self._bash

    @property
    def profile(self):
        return self.bash.profile

    def _replace(self, txt, args={}):
        """

        :param txt:
        :return:
        """
        for key, item in self.__dict__.items():
            if key.upper() == key:
                args[key] = item
        res = j.core.tools.text_replace(content=txt, args=args, text_strip=True)
        return res

    def _execute(self, cmd, die=True, args={}, timeout=3600, replace=True, showout=True, interactive=False, retry=None):
        """

        :param cmd:
        :param die:
        :param showout:
        :param profile:
        :param replace:
        :param interactive:
        :return: (rc, out, err)
        """
        self._log_debug(cmd)
        if replace:
            cmd = self._replace(cmd, args=args)
        if cmd.strip() == "":
            raise j.exceptions.Base("cmd cannot be empty")

        cmd = "cd /tmp/\n. %s\n%s" % (self.profile.profile_path, cmd)
        name = self.__class__._classname
        name = name.replace("builder", "")
        path = "/tmp/builder_%s.sh" % (name)
        self._log_debug("execute: '%s'" % path)

        if die:
            if cmd.find("set -xe") == -1 and cmd.find("set -e") == -1:
                cmd = "set -ex\n%s" % (cmd)

        j.sal.fs.writeFile(path, contents=cmd)

        rc, res, out = j.sal.process.execute(
            "bash %s" % path,
            cwd=None,
            timeout=timeout,
            die=die,
            args=args,
            interactive=interactive,
            replace=False,
            showout=showout,
            retry=retry,
        )
        j.sal.fs.remove(path)
        return (rc, res, out)

    def _copy(
        self,
        src,
        dst,
        deletefirst=False,
        ignoredir=None,
        ignorefiles=None,
        deleteafter=False,
        keepsymlink=True,
        overwrite=True,
    ):
        """

        :param src:
        :param dst:
        :param deletefirst:
        :param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache__']
        :param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]
        :param deleteafter, means that files which exist at destination but not at source will be deleted
        :return:
        """
        src = self._replace(src)
        dst = self._replace(dst)
        if j.builders.tools.file_is_dir:
            j.builders.tools.copyTree(
                src,
                dst,
                keepsymlinks=keepsymlink,
                deletefirst=deletefirst,
                overwriteFiles=True,
                ignoredir=ignoredir,
                ignorefiles=ignorefiles,
                recursive=True,
                rsyncdelete=deleteafter,
                createdir=True,
            )
        else:
            j.builders.tools.file_copy(src, dst, recursive=False, overwrite=overwrite)

    def _write(self, path, txt):
        """
        will use the replace function on text and on path
        :param path:
        :param txt:
        :return:
        """
        path = self._replace(path)
        txt = self._replace(txt)
        j.sal.fs.writeFile(path, txt)

    def _read(self, location):
        """
        will use the replace function on location then read a file from the given location
        :param location: location to read file from
        :return
        """

        location = self._replace(location)
        return j.core.tools.file_text_read(location)

    def _remove(self, path):
        """
        will use the replace function on text and on path
        :param path:
        :return:
        """
        self._log_debug("remove:%s" % path)
        path = self._replace(path)

        j.sal.fs.remove(path)

    def _exists(self, path):
        """
        will use the replace function on text and on path
        :param path:
        :return:
        """
        path = self._replace(path)
        return j.sal.fs.exists(path)

    @property
    def system(self):
        return j.builders.system

    @property
    def tools(self):
        """
        Builder tools is a set of tools to perform the common tasks in your builder (e.g read a file
        , write to a file, execute bash commands and many other handy methods that you will probably need in your builder)
        :return:
        """
        return j.builders.tools

    def reset(self):
        """
        reset the state of your builder, important to let the state checking restart
        and it removes build files (calls a self.clean)
        :return:
        """
        self._done_reset()
        self.clean()

    def state_reset(self):
        """
        reset the state of your builder, all states of builder are gone that way
        :return:
        """
        self._done_reset()

    @builder_method()
    def build(self):
        """
        :return:
        """
        return

    @builder_method()
    def install(self):
        """
        will build as first step
        :return:
        """
        return

    @builder_method()
    def sandbox(self, zhub_client):
        """
        when zhub_client None will look for j.clients.get("test"), if not exist will die
        """
        return

    @property
    def startup_cmds(self):
        """
        is list if j.servers.startupcmd...
        :return:
        """
        return []

    def start(self):
        self.install()
        for startupcmd in self.startup_cmds:
            startupcmd.start()

    def stop(self):
        for startupcmd in self.startup_cmds:
            startupcmd.stop()

    def running(self):
        for startupcmd in self.startup_cmds:
            if startupcmd.is_running() is False:
                return False
        return True

    @builder_method()
    def _flist_create(self, zhub_client, merge_base_flist=""):
        """
        build a flist for the builder and upload the created flist to the hub

        This method builds and optionally upload the flist to the hub

        :param zhub_instance: zerohub client to use to upload the flist, defaults to None if None
        the flist will be created but not uploaded to the hub
        :param merge_base_flist: a base flist to merge the created flist with. If supplied, both merged and normal flists will be uploaded, optional
        :return: the flist url
        """
        if j.core.platformtype.myplatform.platform_is_linux:
            ld_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "lib64/")
            j.builders.tools.dir_ensure(ld_dest)
            self._copy("/lib64/ld-linux-x86-64.so.2", ld_dest)

        self._log_info("uploading flist to the hub")
        flist_url = zhub_client.sandbox_upload(self._classname, self.DIR_SANDBOX)
        if merge_base_flist:
            self._log_info("merging the produced flist with {}".format(merge_base_flist))

            target = "{}_merged_{}".format(self._classname, merge_base_flist.replace("/", "_").replace(".flist", ""))
            flist_name = "{username}/{flist_name}.flist".format(
                username=zhub_client.username, flist_name=self._classname
            )
            flist_url = zhub_client.merge(target, [flist_name, merge_base_flist])

        return flist_url

    @builder_method()
    def _tarfile_create(self):
        tarfile = "/tmp/{}.tar.gz".format(self._classname)
        j.sal.process.execute("tar czf {} -C {} .".format(tarfile, self.DIR_SANDBOX))
        return tarfile

    def clean(self):
        """
        removes all files as result from building
        :return:
        """
        self.uninstall()
        return

    def uninstall(self):
        """
        optional, removes installed, build & sandboxed files
        :return:
        """
        return

    def test(self):
        """
        -  a basic test to see if the build was successfull
        - will automatically call start() at start
        - is optional
        """
        raise j.exceptions.Base("not implemented")

    def test_api(self, ipaddr="localhost"):
        """
        - will test the api on specified ipaddr e.g. rest calls, tcp calls, port checks, ...
        """
        raise j.exceptions.Base("not implemented")

    def test_zos(self, zhub_client, zos_client):
        """

        - a basic test to see if the build was successfull
        - will automatically call sandbox(zhub_client=zhub_client) at start
        - will start the container on specified zos_client with just build flist
        - will call .test_api() with ip addr of the container

        """
        raise j.exceptions.Base("not implemented")
