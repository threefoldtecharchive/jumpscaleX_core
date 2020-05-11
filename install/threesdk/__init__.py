from . import container, simulator, threebot
from . import builder
from . import core
from . import args
import textwrap

# import jsx

__all__ = ["builder", "simulator", "container", "args", "core", "installer", "install", "threebot"]
__version__ = "_unreleased_"

IT = core.core.IT


def install(
    reinstall=False, pull=False, no_interactive=False, threebot=False, identity=None, reset=None, email=None, words=None
):
    """
    Install jumpscale on host (not all platforms supported)
    """
    IT.MyEnv.interactive = not no_interactive
    if reinstall:
        # remove the state
        IT.MyEnv.state_reset()
        force = True
    else:
        force = False

    installer = IT.JumpscaleInstaller()
    installer.install(
        sandboxed=False,
        force=force,
        gitpull=pull,
        threebot=threebot,
        identity=identity,
        reset=reset,
        email=email,
        words=words,
    )
    print("Jumpscale X installed successfully")


def _get_doc_line(doc):
    if not doc:
        return ""
    for line in doc.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _get_doc(doc):
    if not doc:
        return ""
    return textwrap.dedent(doc)
