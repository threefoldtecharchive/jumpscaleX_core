from . import container, simulator
from . import builder
from . import core
from . import args
import textwrap

# import jsx

__all__ = ["builder", "simulator", "container", "install", "args", "core", "installer"]


def install():
    """
    Install 3bot on host
    """
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
