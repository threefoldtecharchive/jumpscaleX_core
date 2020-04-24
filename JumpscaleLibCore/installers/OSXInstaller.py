class OSXInstaller:
    def __init__(self, myenv):
        self._my = myenv
        self._tools = myenv.tools

    def do_all(self, pips_level=3):
        self._my.init()
        self._tools.log("installing OSX version")
        self._my.installers.base.base()
        self._my.installers.base.pips_install(pips_level=pips_level)

    def base(self):
        self._my.init()
        # TODO: check is osx
        self._my.installers.osx.brew_install()
        if (
            not self._tools.cmd_installed("curl")
            or not self._tools.cmd_installed("unzip")
            or not self._tools.cmd_installed("rsync")
        ):
            script = """
            brew install curl unzip rsync tmux libssh2
            """
            # graphviz #TODO: need to be put elsewhere but not in baseinstaller
            self._tools.execute(script, replace=True)
        self._my.installers.base.pips_install(["click, redis"])  # TODO: *1

    def brew_install(self):
        if not self._tools.cmd_installed("brew"):
            cmd = 'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
            self._tools.execute(cmd, interactive=True)

    def brew_uninstall(self):
        self._my.init()
        cmd = 'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/uninstall)"'
        self._tools.execute(cmd, interactive=True)
        toremove = """
        sudo rm -rf /usr/local/.com.apple.installer.keep
        sudo rm -rf /usr/local/include/
        sudo rm -rf /usr/local/etc/
        sudo rm -rf /usr/local/var/
        sudo rm -rf /usr/local/FlashcardService/
        sudo rm -rf /usr/local/texlive/
        """
        self._tools.execute(toremove, interactive=True)
