from . import container, simulator
from . import builder
from . import core
from . import args

# import jsx

__all__ = ["builder", "simulator", "container", "install", "args", "core"]


def install():
    """
    Install 3bot on host
    """
    jsx.install.callback()
