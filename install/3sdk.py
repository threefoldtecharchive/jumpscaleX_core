#!/usr/bin/env python3
import os


from InstallTools import *

from Jumpscale.core.KosmosShell import *

from ptpython.repl import embed


# import grammar


class Core:
    pass


class Application:
    def __init__(self):
        self._in_autocomplete = False


class Logger:
    def _log_error(self, msg, data=None):
        print(msg)


class Jumpscale:
    def __init__(self):
        self.core = Core()
        self.core.tools = Tools
        self.tools = Tools
        self.tools.logger = Logger()
        self.core.myenv = MyEnv
        self.application = Application()


j = Jumpscale()


def shell(loc=True, exit=False, locals_=None, globals_=None):
    import inspect
    from ptpython.repl import embed

    KosmosShellConfig.j = j
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    f = calframe[1]
    if loc:
        print("\n*** file: %s" % f.filename)
        print("*** function: %s [linenr:%s]\n" % (f.function, f.lineno))

    # Tools.clear()
    history_filename = "%s/.jsx_history" % MyEnv.config["DIR_HOME"]
    if not Tools.exists(history_filename):
        Tools.file_write(history_filename, "")
    # locals_= f.f_locals
    # if curframe.f_back.f_back is not None:
    #     locals_=curframe.f_back.f_back.f_locals
    # else:
    # if not locals_:
    #     locals_ = curframe.f_back.f_locals
    # locals_ = self._locals_get(locals_)
    # if not globals_:
    #     globals_ = curframe.f_back.f_globals
    if exit:
        sys.exit(embed(globals_, locals_, configure=ptconfig, history_filename=history_filename))
    else:
        embed(globals_, locals_, configure=ptconfig, history_filename=history_filename)


class Docker:
    def test(self, name=""):
        """
        lets check the docs

        param: name ...

        """
        print(name)


docker = Docker()


if __name__ == "__main__":

    shell(locals_=locals(), globals_=globals())
