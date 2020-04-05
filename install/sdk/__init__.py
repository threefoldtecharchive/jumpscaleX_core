__all__ = ["container"]


import os
import sys
import shutil
import urllib
from urllib.request import urlopen
from urllib.error import URLError
from importlib import util
import time
import json

DEFAULT_BRANCH = "unstable"
os.environ["LC_ALL"] = "en_US.UTF-8"


def _name_clean(name):
    name = name.lower()
    if "." not in name:
        name = name + ".3bot"
    return name


class jsx:
    def __init__(self):
        self._data = None

    @property
    def phonebook(self):
        if not self._data:
            url = "https://explorer.testnet.grid.tf/explorer/users"
            with urlopen(url) as resp:
                if resp.status != 200:
                    raise RuntimeError("fail to download users metadata")
                data = resp.read().decode("utf-8")
                self._data = json.loads(data)
        return self._data

    def _email_clean(self, email):
        email = email.lower()
        if "@" not in email:
            raise IT.Tools.exceptions.Input("email needs to have @ inside, now '%s'" % email)
        return email

    def phonebook_check(self, name, email):
        name_res = None
        email_res = None
        name = _name_clean(name)
        email = self._email_clean(email)
        for d in self.phonebook:
            if d["name"] == name:
                name_res = d
            if d["email"] == email:
                email_res = d
        return name_res, email_res

    def can_get_url(self, url, timeout=5):
        """check if we can get a url

        :param url: url
        :type url: str
        :param timeout: timeout in seconds, defaults to 5
        :type timeout: int, optional
        :return: url response or None
        :rtype: None or HTTPResponse
        """
        try:
            return urlopen(url, timeout=timeout)
        except URLError:
            pass

    def load_install_tools(self, branch=None, reset=False):
        # get current install.py directory

        path = "/sandbox/code/github/threefoldtech/jumpscaleX_core/install/InstallTools.py"
        if not os.path.exists(path):
            path = os.path.expanduser("~/sandbox/code/github/threefoldtech/jumpscaleX_core/install/InstallTools.py")

        if not branch:
            branch = DEFAULT_BRANCH
        # first check on code tools
        if not os.path.exists(path):
            rootdir = os.path.dirname(sys.executable)
            path = os.path.join(rootdir, "InstallTools.py")
            # now check on path next to jsx
            if not os.path.exists(path) or reset:  # or path.find("/code/") == -1:
                url = (
                    "https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/%s/install/InstallTools.py"
                    % branch
                )

                # fallback to default branch if installation is being done for another branch that doesn't exist in core
                if branch != DEFAULT_BRANCH and not self.can_get_url(url):
                    url = (
                        "https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/%s/install/InstallTools.py"
                        % DEFAULT_BRANCH
                    )

                with urlopen(url) as resp:
                    if resp.status != 200:
                        raise RuntimeError("fail to download InstallTools.py")
                    with open(path, "w+") as f:
                        f.write(resp.read().decode("utf-8"))
                    print("DOWNLOADED INSTALLTOOLS TO %s" % path)

        spec = util.spec_from_file_location("IT", path)
        IT = spec.loader.load_module()
        IT.MyEnv.init()
        return IT


jsx = jsx()
IT = jsx.load_install_tools()
IT.MyEnv.interactive = True  # std is interactive
Tools = IT.Tools
MyEnv = IT.MyEnv


class JSXEnv:
    def __init__(self):
        self._DF = IT.DockerFactory

    @property
    def DF(self):
        if not self._DF:
            self._DF.init()
        return self._DF


e = JSXEnv()


def jumpscale_get(die=True):
    # jumpscale need to be available otherwise cannot do
    try:
        from Jumpscale import j
    except Exception:
        if die:
            raise RuntimeError("ERROR: cannot use jumpscale yet, has not been installed")
        return None
    return j


def container_get(name="3bot", delete=False, jumpscale=True, install=False, mount=True):
    IT.MyEnv.sshagent.key_default_name
    e.DF.init()
    docker = e.DF.container_get(name=name, image="threefoldtech/3bot2", start=True, delete=delete, mount=mount)
    # print(docker.executor.config)
    force = False
    if not docker.executor.exists("/sandbox/cfg/keys/default/key.priv"):
        jumpscale = True
        install = True
        force = True
    if jumpscale:
        installer = IT.JumpscaleInstaller()
        installer.repos_get(pull=False)
        if install:
            docker.install_jumpscale(force=force)
    return docker


def install(
    branch=None, reinstall=False, pull=False, no_interactive=False, prebuilt=False, threebot=False, identity=None,
):
    """
    install jumpscale in the local system (only supported for Ubuntu 18.04+ and mac OSX, use container install method otherwise.
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '


    """

    # print("DEBUG:: no_sshagent", no_sshagent, "configdir", configdir)  #no_sshagent=no_sshagent
    # IT.MyEnv.interactive = True
    _configure(no_interactive=no_interactive)
    if reinstall:
        # remove the state
        IT.MyEnv.state_reset()
        force = True
    else:
        force = False

    installer = IT.JumpscaleInstaller()
    assert prebuilt is False  # not supported yet
    installer.install(
        sandboxed=False,
        force=force,
        gitpull=pull,
        prebuilt=prebuilt,
        branch=branch,
        threebot=threebot,
        identity=identity,
    )
    print("Jumpscale X installed successfully")


def jumpscale_code_get(branch=None, pull=False, reset=False):
    """
    install jumpscale in the local system (only supported for Ubuntu 18.04+ and mac OSX, use container install method otherwise.
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '

    """
    # IT.MyEnv.interactive = True
    # _configure(no_interactive=True)
    if not branch:
        branch = IT.DEFAULT_BRANCH
    installer = IT.JumpscaleInstaller()
    installer.repos_get(pull=pull, reset=reset)
    # IT.Tools.shell()
