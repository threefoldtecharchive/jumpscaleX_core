from . import container, simulator
from . import sdk
import jsx
__all__ = ["sdk", "simulator", "container", "install"]


def install():
    """
    Install 3bot on host
    """
    jsx.install.callback()
