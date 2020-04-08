from . import container, simulator
from . import sdk
import jsx
__all__ = ["container", "install", "sdk", "simulator"]


def install():
    """
    Install 3bot on host
    """
    jsx.install.callback()
