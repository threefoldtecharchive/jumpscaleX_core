class OSXInstaller:
    @staticmethod
    def do_all(pips_level=3):
        MyEnv.init()
        Tools.log("installing OSX version")
        OSXInstaller.base()
        BaseInstaller.pips_install(pips_level=pips_level)

    @staticmethod
    def base():
        MyEnv.init()
        OSXInstaller.brew_install()
        if not Tools.cmd_installed("curl") or not Tools.cmd_installed("unzip") or not Tools.cmd_installed("rsync"):
            script = """
            brew install curl unzip rsync tmux libssh2
            """
            # graphviz #TODO: need to be put elsewhere but not in baseinstaller
            Tools.execute(script, replace=True)
        BaseInstaller.pips_install(["click, redis"])  # TODO: *1

    @staticmethod
    def brew_install():
        if not Tools.cmd_installed("brew"):
            cmd = 'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
            Tools.execute(cmd, interactive=True)

    @staticmethod
    def brew_uninstall():
        MyEnv.init()
        cmd = 'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/uninstall)"'
        Tools.execute(cmd, interactive=True)
        toremove = """
        sudo rm -rf /usr/local/.com.apple.installer.keep
        sudo rm -rf /usr/local/include/
        sudo rm -rf /usr/local/etc/
        sudo rm -rf /usr/local/var/
        sudo rm -rf /usr/local/FlashcardService/
        sudo rm -rf /usr/local/texlive/
        """
        Tools.execute(toremove, interactive=True)
