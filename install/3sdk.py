#!/usr/bin/env python3
import sys

from ptpython.repl import embed

from sdk import Tools, MyEnv
from sdk.shell import ptconfig
from sdk import container, install

import jedi

# for auto-completion data
# also, jedi and parso hooks need to be available
# for autoc-completion to work with pyinstaller build
jedi.preload_module("sdk")


def shell(loc=True, exit=False, locals_=None, globals_=None):
    import inspect

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    f = calframe[1]
    if loc:
        print("\n*** file: %s" % f.filename)
        print("*** function: %s [linenr:%s]\n" % (f.function, f.lineno))

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
