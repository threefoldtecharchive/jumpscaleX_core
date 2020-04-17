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
