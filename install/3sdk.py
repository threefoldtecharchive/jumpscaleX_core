#!/usr/bin/env python3
import sys
import jedi
import sdk as _sdk

from ptpython.repl import embed

from functools import partial
from sdk.shell import ptconfig
from sdk import container, builder, simulator, install, args, core, installer, _get_doc_line  # pylint: disable=F401

IT = core.core.IT


from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import HTML


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
        if name[0].lower() != name[0]:
            continue

        is_module = inspect.ismodule(obj)
        if is_module and level != 0:
            continue

        spaces = " " * level

        if is_module:
            doc += f"{spaces}<ansibrightblue>{name}</ansibrightblue>"
        elif getattr(obj, "__property__", False):
            doc += f"{spaces}<ansicyan>{name}</ansicyan>"
        else:
            doc += f"{spaces}<ansigreen>{name}</ansigreen>"

        if obj.__doc__:
            try:
                # only get first line of member docstring
                first_line = _get_doc_line(obj.__doc__)
                doc += f": {first_line}"
            except IndexError:
                pass

        doc = f"{doc}\n"

        if is_module:
            doc += get_doc(obj, level=level + size)

    return doc


def info():
    print_formatted_text(HTML(get_doc(_sdk)))


def shell(loc=False, exit=False, locals_=None, globals_=None, expert=False):
    import inspect

    if not expert:
        _sdk.__all__.remove("builder")
        _sdk.__all__.remove("installer")

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
    # the shell should only show d... j...  (no capitals at start of sentence)
    # logger needs to be redirected properly
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--expert", default=False, action="store_true")
    options = parser.parse_args()
    shell(locals_=locals(), globals_=globals(), expert=options.expert)
