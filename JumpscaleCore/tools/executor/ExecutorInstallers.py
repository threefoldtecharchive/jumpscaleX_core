from Jumpscale import j

from functools import wraps


class executor_method(object):
    """A Decorator to be used in all installer methods
    this will provide:
    1- State check to make sure not to do one action multiple times
    """

    def __init__(self, *args, **kwargs_):

        if "log" in kwargs_:
            self.log = j.data.types.bool.clean(kwargs_["log"])
        else:
            self.log = True
        if "done_check" in kwargs_:
            self.done_check = j.data.types.bool.clean(kwargs_["done_check"])
        else:
            self.done_check = True

    def already_done(self, func, installer, key, reset):
        """ Check if this method was already done or not

        *Note* if you pass reset=True to any method it will be executed again
        :param func: the function called
        :param installer: the installer used
        :return: True means it was already done and you don't need to redo, False means not done before or reset=True
        """
        if not self.done_check:
            # if this is given will not do a done check
            return False

        if reset or not installer.executor.state_exists("installer_%s" % key):
            return False
        return True

    def __call__(self, func):
        @wraps(func)
        def wrapper_action(installer, *args, **kwargs):
            """The main wrapper method for the decorator, it will do:
            1- check if the method is going to be executed or it's already done before
            2- make sure that the previous method were executed in the correct order
            3- choose the correct env file for the action
            4- prepare any needed parameters AKA zerohub client in case of creating a flist
            :param installer: the installer self
            :param args: args passed to the method
            :param kwargs: kwargs passed to the method
            :return: if the method was already done it will return BuilderBase.ALREADY_DONE_VALUE
            """
            if len(args) > 0:
                raise j.exceptions.Base("only use kwargs")
            name = func.__name__
            kwargs_without_reset = {key: value for key, value in kwargs.items() if key not in ["reset", "self"]}
            done_key = name + "_" + j.data.hash.md5_string(str(kwargs_without_reset))
            reset = kwargs.get("reset", False)

            if self.already_done(func, installer, done_key, reset):
                return installer.executor.state_get("installer_%s" % done_key)

            if name is not "base":
                installer.base()

            if self.log:
                installer._log_debug("execute:%s with args:%s" % (name, kwargs_without_reset))

            res = func(installer, **kwargs_without_reset)

            installer.executor.state_set("installer_%s" % done_key, res)

            return res

        return wrapper_action


class ExecutorInstallers(j.baseclasses.object):
    def _init(self, executor=None, **kwargs):

        self.executor = executor

    @executor_method()
    def kosmos(self):
        self.jumpscale()
        j.shell()

    @executor_method()
    def base(self):
        self.executor.execute("apt-get update")
        self.executor.execute(
            'DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -q -o DEBIAN_PRIORITY=critical -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confold"',
            interactive=True,
        )

    def jumpscale_test(self):
        self.executor.execute_jumpscale("j.tools.executor.local.test()")

    @executor_method()
    def secure(self, web=True):
        if web:
            C = """
            apt-get install ufw -y
            echo "y" | ufw reset
            ufw allow 22/tcp
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw allow 9900/tcp
            #mosh
            ufw allow 6000:6100/udp
            echo "y" | ufw enable
            """
        else:
            C = """
            apt-get install ufw -y
            echo "y" | ufw reset
            ufw allow 22/tcp
            ufw allow 6000:6100/udp
            ufw allow 9900/tcp
            echo "y" | ufw enable
            """
        self.executor.execute(C)

    @executor_method()
    def mosh(self):
        self.executor.execute("apt-get install mosh -y")
        self.secure(web=False)

    @executor_method()
    def jumpscale(self):
        self.executor.execute(
            "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/%s/install/jsx.py\?$RANDOM > /tmp/jsx"
            % j.core.myenv.DEFAULT_BRANCH
        )
        self.executor.execute("chmod +x /tmp/jsx")
        cmd = "cd /tmp;python3 jsx configure --sshkey %s -s" % j.core.myenv.sshagent.key_default_name
        self.executor.execute(cmd, interactive=True)
        self.executor.execute("/tmp/jsx install -s", interactive=True)

    @executor_method()
    def threebot(self):
        self.executor.execute_jumpscale("j.servers.threebot.test()")

    @executor_method()
    def jumpscale_container(self):
        self.executor.execute(
            "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/%s/install/jsx.py\?$RANDOM > /tmp/jsx"
            % j.core.myenv.DEFAULT_BRANCH
        )
        self.executor.execute("chmod 777 /tmp/jsx")
        self.executor.execute("/tmp/jsx container_install", interactive=True)

    def _check_base(self):
        if not self.__check_base:

            def do():
                if self.state_exists("check_base") is False:
                    C = """
                    if ! grep -Fq "deb http://mirror.unix-solutions.be/ubuntu/ bionic" /etc/apt/sources.list; then
                        echo >> /etc/apt/sources.list
                        echo "# Jumpscale Setup" >> /etc/apt/sources.list
                        echo deb http://mirror.unix-solutions.be/ubuntu/ bionic main universe multiverse restricted >> /etc/apt/sources.list
                    fi
                    apt-get update
                    apt-get install rsync curl wget -y
                    apt-get install git -y
                    # apt-get install mosh -y
                    """
                    self.execute(j.core.text.strip(C))
                    self.state_set("check_base")
                return "OK"

            self.cache.get("_check_base", method=do, expire=3600, refresh=False, retry=2, die=True)

            self.__check_base = True
