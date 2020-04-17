import os

from . import container, simulator
from . import builder
from . import core
from . import args
import textwrap


os.environ["LC_ALL"] = "en_US.UTF-8"

__all__ = ["builder", "simulator", "container", "args", "core", "installer", "install"]


def install():
    """
    Install jumpscale on host (not all platforms supported)
    """
    # TODO: needs to be implemented
    jsx.install.callback()


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
