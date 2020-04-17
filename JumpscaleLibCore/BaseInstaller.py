import os


class BaseInstaller:
    def __init__(self, myenv):
        self._my = myenv
        self._tools = self._my.tools

    def install(self, force=False, sandboxed=False, branch=None, pips_level=3):

        if force:
            self._my.state_delete("install")

        if self._my.state_get("install"):
            return  # nothing to do

        self._my.installers.base.base()
        if self._my.platform() == "linux":
            if not sandboxed:
                self._my.installers.ubuntu.do_all()
            else:
                raise self._tools.exceptions.Base("not ok yet")
                self._my.installers.ubuntu.base(pips_level=pips_level)
        elif "darwin" in self._my.platform():
            if not sandboxed:
                self._my.installers.osx.do_all(pips_level=pips_level)
            else:
                raise self._tools.exceptions.Base("not ok yet")
                self._my.installers.osx.base()
        else:
            raise self._tools.exceptions.Base("only OSX and Linux Ubuntu supported.")

        for profile_name in [".bash_profile", ".profile"]:
            # BASHPROFILE
            if sandboxed:
                env_path = "%s/%s" % (self._my.config["DIR_HOME"], profile_name)
                if self._tools.exists(env_path):
                    bashprofile = self._tools.file_text_read(env_path)
                    cmd = "source %s/env.sh" % self._my._basedir_get()
                    if bashprofile.find(cmd) != -1:
                        bashprofile = bashprofile.replace(cmd, "")
                        self._tools.file_write(env_path, bashprofile)
            else:
                # if not sandboxed need to remove old python's from bin dir
                self._tools.execute("rm -f {DIR_BASE}/bin/pyth*", die_if_args_left=True)
                env_path = "%s/%s" % (self._my.config["DIR_HOME"], profile_name)
                if not self._tools.exists(env_path):
                    bashprofile = ""
                else:
                    bashprofile = self._tools.file_text_read(env_path)
                cmd = "source %s/env.sh" % self._my._basedir_get()
                if bashprofile.find(cmd) == -1:
                    bashprofile += "\n%s\n" % cmd
                    self._tools.file_write(env_path, bashprofile)

        ji = self._my.installers.jumpscale()
        print("- get sandbox repos from git")
        ji.repos_get(pull=False, branch=branch)
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
            self._tools.execute(script, interactive=self._my.interactive, die_if_args_left=True, replace=True)

        else:

            # install the sandbox

            raise self._tools.exceptions.Base("not done yet")

            script = """
            cd {DIR_BASE}
            rsync -ra {DIR_BASE}/code/github/threefoldtech/sandbox_base/base/ {DIR_BASE}/
            mkdir -p root
            """
            self._tools.execute(script, interactive=self._my.interactive, die_if_args_left=True)

            if self._my.platform() == "darwin":
                reponame = "sandbox_osx"
            elif self._my.platform() == "linux":
                reponame = "sandbox_ubuntu"
            else:
                raise self._tools.exceptions.Base("cannot install, self._my.platform() now found")

            self._tools.code_github_get(repo=reponame, branch=["master"])

            script = """
            set -e
            cd {DIR_BASE}
            rsync -ra code/github/threefoldtech/{REPONAME}/base/ .
            mkdir -p root
            mkdir -p var
            """
            args = {}
            args["REPONAME"] = reponame

            self._tools.execute(script, interactive=self._my.interactive, args=args, die_if_args_left=True)

            script = """
            set -e
            cd {DIR_BASE}
            source env.sh
            python3 -c 'print("- PYTHON OK, SANDBOX USABLE")'
            """
            self._tools.execute(script, interactive=self._my.interactive, die_if_args_left=True)

            self._tools.log("INSTALL FOR BASE OK")

        self._my.state_set("install")

    def base(self):

        if self._my.state_get("generic_base"):
            return

        if not os.path.exists(self._my.config["DIR_TEMP"]):
            os.makedirs(self._my.config["DIR_TEMP"], exist_ok=True)

        script = """

        mkdir -p {DIR_TEMP}/scripts
        mkdir -p {DIR_VAR}/log

        """
        self._tools.execute(script, interactive=True, die_if_args_left=True)

        if self._my.platform_is_osx:
            self._my.installers.osx.base()
        elif self._my.platform_is_linux:
            self._my.installers.ubuntu.base()
        else:
            print("Only ubuntu & osx supported")
            os.exit(1)

        self._my.state_set("generic_base")

    def pips_list(self, level=3):
        """
        level0 is only the most basic
        1 in the middle (recommended)
        2 is all pips
        """

        # ipython==7.5.0 ptpython==2.0.4 prompt-toolkit==2.0.9

        pips = {
            # level 0: most basic needed
            0: [
                "mypi",
                "cached_property",
                "captcha",
                "certifi",
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
                "future>=0.15.0",
                "geopy",
                "geocoder",
                "gevent >= 1.2.2",
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
                "cython",
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
                "prompt-toolkit==2.0.9",
                "pygments-markdown-lexer",
                "wsgidav",
                "bottle==0.12.17",  # why this version?
                "beaker",
                "Mnemonic",
                "xmltodict",
                "sonic-client",
                "watchdog_gevent",
                "python-digitalocean",
                "ujson",
                "stellar-sdk",
                "packet-python>=1.37",
                "gevent-websocket",
                "base58",
                "ansicolors",
                "better_exceptions",
            ],
            # level 1: in the middle
            1: [
                "Brotli>=0.6.0",
                "gipc",
                # "blosc>=1.5.1",  #don't think we use it, I hope
                "scikit-build",
                # "cmake",  #DO WE NEED THIS??? better not, takes for ever
                "zerotier>=1.1.2",
                "python-jose>=2.0.1",
                "itsdangerous>=0.24",
                "jsonschema>=2.5.1",
                "graphene>=2.0",
                "ovh>=0.4.7",
                # "uvloop>=0.8.0",  #think is not used
                "pycountry",
                "pycountry_convert",
                "cson>=0.7",
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
                "google-api-python-client",
            ],
        }

        res = []

        for piplevel in pips:
            if piplevel <= level:
                res += pips[piplevel]

        return res

    def pips_install(self, items=None, pips_level=3):
        if not items:
            items = self._my.installers.base.pips_list(pips_level)
            self._my.state_set("pip_zoos")
        for pip in items:
            if not self._my.state_get("pip_%s" % pip):
                C = "pip3 install '%s'" % pip  # --user
                self._tools.execute(C, die=True, retry=3)
                self._my.state_set("pip_%s" % pip)
        # C = "pip3 install -e 'git+https://github.com/threefoldtech/0-hub#egg=zerohub&subdirectory=client'"
        # self._tools.execute(C, die=True)

    def code_copy_script_get(self):
        CMD = """
        cd /
        rm -rf /sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/threebot
        rm -rf  /sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/zerobot/alerta
        [ -d "/sandbox/code/github" ] && rsync -rav --exclude '__pycache__' --exclude '.git' --exclude '.idea' --exclude '*.pyc' /sandbox/code/github/threefoldtech/ /sandbox/code_org/

        """
        return self._tools.text_strip(CMD, replace=False)

    def cleanup_script_get(self):
        CMD = """
        cd /
        rm -f /sandbox/cfg/.configured
        rm -f /tmp/cleanedup
        rm -f /root/.jsx_history
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
        rm -rf /var/cache/luarocks
        apt remove nodejs -y
        apt-get clean -y
        apt-get autoremove --purge -y
        rm -rf /sandbox/openresty/pod
        rm -rf /sandbox/openresty/site
        rm -rf /sandbox/var
        mkdir -p /sandbox/var
        rm -f /sandbox/cfg/bcdb_config
        rm -f /sandbox/cfg/schema_meta.msgpack
        rm -rf /sandbox/cfg/bcdb
        rm -rf /sandbox/cfg/keys
        rm -rf /sandbox/cfg/nginx/default_openresty_threebot/static/weblibs
        rm -rf /sandbox/root
        rm -rf /usr/src
        #remove nodejs things
        find / | grep -E "(yarn|node_modules)" | xargs rm -rf 2>&1 > /dev/null
        rm -rf /usr/local/share/jupyter/lab/staging
        rm -f /sandbox/bin/openresty.old
        #remove apt cache
        rm -rf /var/lib/apt/lists
        mkdir -p /var/lib/apt/lists
        #non neccesary files
        find / | grep -E "(__pycache__|\.bak$|\.pyc$|\.pyo$|\.rustup|\.cargo)" | xargs rm -rf 2>&1 > /dev/null
        #IMPORTANT remove secret from config file
        if test -f "/sandbox/cfg/jumpscale_config.toml"; then
            sed -i -r 's/^SECRET =.*/SECRET =/' /sandbox/cfg/jumpscale_config.toml
        fi
        """
        return self._tools.text_strip(CMD, replace=False)

    def cleanup_script_developmentenv_get(self):
        CMD = """
        apt remove gcc -y
        apt remove rustc -y
        apt remove llvm -y
        rm -rf  /sandbox/go
        rm -rf  /sandbox/go_proj
        apt-get remove --auto-remove golang-go -y
        rm -rf /usr/lib/x86_64-linux-gnu/libLLVM-6.0.so.1
        rm -rf /usr/lib/llvm-6.0
        rm -rf /usr/lib/llvm-9.0
        rm -rf /usr/lib/llvm-*.0
        rm -rf /usr/lib/llvm-*
        rm -rf /usr/lib/gcc
        find / | grep -E "(LLVM|llvm/)" | xargs rm -rf
        export SUDO_FORCE_REMOVE=no
        apt-mark manual wireguard-tools
        apt-mark manual sudo
        apt-get autoremove --purge -y
        rm -rf /var/lib/apt/lists
        mkdir -p /var/lib/apt/lists
        # rm -rf /sandbox/nodejs
        #remove libgcc
        rm -rf /usr/lib/gcc

        """
        return self._tools.text_strip(CMD, replace=False)
