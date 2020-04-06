#!/usr/bin/env python3
import sys
import jedi
import sdk

from ptpython.repl import embed

from sdk import Tools, MyEnv
from sdk.shell import ptconfig
from sdk import container, install


# for auto-completion data
# also, jedi and parso hooks need to be available
# for autoc-completion to work with pyinstaller build
jedi.preload_module("sdk")


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
    doc = ""

    for name in root_module.__all__:
        obj = getattr(root_module, name)
        is_module = hasattr(obj, "__all__")

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
    print(get_doc(sdk))


def shell(loc=False, exit=False, locals_=None, globals_=None):
    import inspect

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    f = calframe[1]
    if loc:
        print("\n*** file: %s" % f.filename)
        print("*** function: %s [linenr:%s]\n" % (f.function, f.lineno))

    print("Welcome to sdk shell, for available modules, call info()")

    # Tools.clear()
    history_filename = "%s/.jsx_sdk_history" % MyEnv.config["DIR_HOME"]
    if not Tools.exists(history_filename):
        Tools.file_write(history_filename, "")

    if exit:
        sys.exit(embed(globals_, locals_, configure=ptconfig, history_filename=history_filename))
    else:
        embed(globals_, locals_, configure=ptconfig, history_filename=history_filename)


if __name__ == "__main__":

    # the shell should only show d... j...  (no capitals at start of sentense)
    # logger needs to be redirected properly

    shell(locals_=locals(), globals_=globals())
