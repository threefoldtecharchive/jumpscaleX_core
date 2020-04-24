import os


class UbuntuInstaller:
    def __init__(self, myenv):
        self._my = myenv
        self._tools = myenv.tools

    def do_all(self, prebuilt=False, pips_level=3):
        self._tools.log("installing Ubuntu version")

        self._my.installers.ubuntu.ensure_version()
        self._my.installers.ubuntu.base()
        # UbuntuInstaller.ubuntu_base_install()
        if not prebuilt:
            self._my.installers.ubuntu.python_dev_install()
        self._my.installers.ubuntu.apts_install()
        if not prebuilt:
            self._my.installers.base.pips_install(pips_level=pips_level)

    def ensure_version(self):
        if not os.path.exists("/etc/lsb-release"):
            raise self._tools.exceptions.Base("Your operating system is not supported")

        return True

    def base(self):
        self._my.init()

        if self._my.state_get("base"):
            return

        rc, out, err = self._tools.execute("lsb_release -a")
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
            self._tools.execute(script, interactive=True, die=False)

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
        self._tools.execute(script, interactive=True)

        if bionic and not self._my._docker.indocker():
            self._my.installers.ubuntu.docker_install()

        self._my.state_set("base")

    def docker_install(self):
        if self._my.state_get("ubuntu_docker_install"):
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
        self._tools.execute(script, interactive=True)
        self._my.state_set("ubuntu_docker_install")

    def python_dev_install(self):
        if self._my.state_get("python_dev_install"):
            return

        self._tools.log("installing jumpscale tools")

        script = """
        cd /tmp
        apt-get install -y build-essential
        #apt-get install -y python3.8-dev


        """
        rc, out, err = self._tools.execute(script, interactive=True, timeout=300)
        if rc > 0:
            # lets try other time
            rc, out, err = self._tools.execute(script, interactive=True, timeout=300)
        self._my.state_set("python_dev_install")

    def apts_list(self):
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

    def apts_install(self):
        for apt in self._my.installers.ubuntu.apts_list():
            if not self._my.state_get("apt_%s" % apt):
                command = "apt-get install -y %s" % apt
                self._tools.execute(command, die=True)
                self._my.state_set("apt_%s" % apt)
