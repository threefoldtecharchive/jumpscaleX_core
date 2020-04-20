"""core configuration"""
__all__ = ["branch", "redis"]


class Core:
    def __init__(self):
        self._default_branch = "master"
        self.branch = "development"
        self.load()

    def load(self):
        self.IT = self._load_install_tools()
        self.IT.MyEnv.interactive = True  # std is interactive

    def _load_install_tools(self, reset=False):
        # get current install.py directory
        from . import InstallTools as IT
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


def redis():
    """
    start redis so it will remember our secret and other arguments
    """
    core.IT.RedisTools._core_get()


branch.__property__ = True
