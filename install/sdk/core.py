from importlib import util
import os
from urllib.request import urlopen
import requests

__all__ = ["branch"]


class Core:
    def __init__(self):
        self.branch = "unstable"
        self.load()

    def load(self):
        self.IT = self._load_install_tools()
        self.IT.MyEnv.interactive = True  # std is interactive

    def _load_install_tools(self, reset=False):
        # get current install.py directory

        path = "/sandbox/code/github/threefoldtech/jumpscaleX_core/install/InstallTools.py"
        if not os.path.exists(path):
            path = os.path.expanduser("~/sandbox/code/github/threefoldtech/jumpscaleX_core/install/InstallTools.py")

        # first check on code tools
        if not os.path.exists(path):
            rootdir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(rootdir, "InstallTools.py")
            # now check on path next to jsx
            if not os.path.exists(path) or reset:  # or path.find("/code/") == -1:
                url = f"https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/{self.branch}/install/InstallTools.py"

                # fallback to default branch if installation is being done for another branch that doesn't exist in core
                if branch != branch and requests.get(url).status_code == 404:
                    url = (
                        "https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/%s/install/InstallTools.py"
                        % branch
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


core = Core()


def branch(val=""):
    """
    branch for the code we use normally development or unstable
    """
    if not val:
        return core.branch
    else:
        if core.branch != val:
            core.branch = val
            print(" - load the IT tools")
            core.load()
