#!/usr/bin/env python3
import sys
import jedi
import sdk as _sdk

from ptpython.repl import embed

from jsx import IT
from functools import partial
from sdk.shell import ptconfig
from sdk import container, sdk, simulator, install  # pylint: disable=F401


# for auto-completion data
# also, jedi and parso hooks need to be available
# for autoc-completion to work with pyinstaller build
jedi.preload_module("_sdk")


def get_doc(root_module, level=0, size=4):
    """get a formatted docstring from a module
    this will loop over __all__self.

    :param root_module: root module
    :type root_module: module
    :param level: spacing level, defaults to 0
    :type level: int, optional
    :param level: spacing size, defaults to 4
    :type level: int, optional
    :return: docstring
    :rtype: str
    """
    import inspect
    doc = ""

    if hasattr(root_module, "__all__"):
        members = [(name, getattr(root_module, name)) for name in root_module.__all__]
    else:
        members = inspect.getmembers(root_module)
    for name, obj in members:
        if name.startswith("_"):
            continue
        is_module = inspect.ismodule(obj)
        if is_module and level != 0:
            continue

        spaces = " " * level
        doc += f"{spaces}{name}"

        if is_module:
            doc += " (module)"

        if obj.__doc__:
            try:
                # only get first line of member docstring
                first_line = obj.__doc__.split("\n")[1].strip()
                doc += f": {first_line}"
            except IndexError:
                pass

        doc = f"{doc}\n"

        if is_module:
            doc += get_doc(obj, level=level + size)

    return doc


def info():
    print(get_doc(_sdk))


def shell(loc=False, exit=False, locals_=None, globals_=None, expert=False):
    import inspect
    if not expert:
        _sdk.__all__.remove("container")

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    f = calframe[1]
    if loc:
        print("\n*** file: %s" % f.filename)
        print("*** function: %s [linenr:%s]\n" % (f.function, f.lineno))

    print("Welcome to sdk shell, for available modules, call info()")

    history_filename = "%s/.jsx_sdk_history" % IT.MyEnv.config["DIR_HOME"]
    if not IT.Tools.exists(history_filename):
        IT.Tools.file_write(history_filename, "")

    myptconfig = partial(ptconfig, expert=expert)
    result = embed(globals_, locals_, configure=myptconfig, history_filename=history_filename)
    if exit:
        sys.exit(result)
    return result


if __name__ == "__main__":
    # the shell should only show d... j...  (no capitals at start of sentense)
    # logger needs to be redirected properly
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--expert", default=False, action="store_true")
    options = parser.parse_args()
    shell(locals_=locals(), globals_=globals(), expert=options.expert)
