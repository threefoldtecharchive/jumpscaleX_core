from Jumpscale import j
import os
import fnmatch
from pathlib import Path
from Jumpscale.core.generator.JSGenerator import *
from .FixerReplace import FixerReplacer

# ACTIONS
## R = Replace
## RI = Replace case insensitive

JSBASE = j.baseclasses.object


class Fixer(j.baseclasses.object):

    __jslocation__ = "j.tools.fixer"

    def _init(self, **kwargs):
        self.generator = JSGenerator(j)
        self.replacer = FixerReplacer()

    def _find_changes(self):
        """
        kosmos 'j.tools.fixer.find_changes()'
        :return:
        """

        os.environ["JSRELOAD"] = "1"
        os.environ["JSGENERATE_DEBUG"] = "1"

        def do(jsmodule, classobj, nr, line, args):

            changed, line2 = self.line_process(line)
            if changed:
                jsmodule.line_change_add(nr, line, line2)
            return args

        args = {}
        args = self.generator.generate(methods_find=True, action_method=do, action_args=args)

        self.generator.report()

        print(self.generator.md.line_changes)

    def find_changes(self, path=None, extensions=["py", "txt", "md"], recursive=True):
        """
        kosmos 'j.tools.fixer.find_changes()'
        :return:
        """

        if path is None:
            self._find_changes()

            # important to generate the normal non debug version
            os.environ["JSGENERATE_DEBUG"] = "0"
            self.generator.generate()
        else:
            self.replacer.dir_process(path=path, extensions=extensions, recursive=recursive, write=False)

    def write_changes(self, path=None, extensions=["py", "txt", "md"], recursive=True):
        """
        kosmos 'j.tools.fixer.write_changes()'
        BE CAREFULL THIS WILL WRITE THE CHANGES AS FOUND IN self.find_changes
        """
        if path is None:
            self._find_changes()

            for jsmodule in self.generator.md.jsmodules.values():
                jsmodule.write_changes()

            # important to generate the normal non debug version
            os.environ["JSGENERATE_DEBUG"] = "0"
            self.generator.generate()
        else:
            self.replacer.dir_process(path=path, extensions=extensions, recursive=recursive, write=True)

    def line_process(self, line):
        # self._log_debug("lineprocess:%s"%line)
        return self.replacer.line_process(line)
