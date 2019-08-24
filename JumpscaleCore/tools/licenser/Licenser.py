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


class Licenser(j.baseclasses.object):

    __jslocation__ = "j.tools.licenser"

    def __init__(self):
        JSBASE.__init__(self)
        self.replacer = FixerReplacer()

    def do(self, path=None, write=False, addlicense=True):
        """
        kosmos 'j.tools.licenser.do(write=True,addlicense=False)'
        kosmos 'j.tools.licenser.do()'
        :param path:
        :param write:
        :return:
        """
        if not path:
            self.replacer.dir_process(
                path="/sandbox/code/github/threefoldtech/jumpscaleX", write=True, addlicense=False
            )
            self.replacer.dir_process(
                path="/sandbox/code/github/threefoldtech/digitalmeX", write=True, addlicense=False
            )
            self.do("/sandbox/code/github/threefoldtech/jumpscaleX", write=write, addlicense=addlicense)
            self.do("/sandbox/code/github/threefoldtech/digitalmeX", write=write, addlicense=addlicense)
        else:
            for path2 in j.sal.fs.listFilesInDir(path, filter=".gpl3", recursive=True):
                header = j.sal.fs.readFile(path2)
                if header.strip() == "":
                    header = None
                path3 = j.sal.fs.getDirName(path2)
                self.replacer.dir_process(path=path3, write=write, header=header, addlicense=addlicense)
