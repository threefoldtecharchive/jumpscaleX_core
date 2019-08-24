import os
from pathlib import Path


class Dirs(object):
    """
    for backwards compatibility
    """

    def __init__(self, j):
        self._j = j
        self.BASEDIR = self._j.core.myenv.config["DIR_BASE"]
        self.TMPDIR = self._j.core.myenv.config["DIR_TEMP"]
        self.VARDIR = self._j.core.myenv.config["DIR_VAR"]
        self.CFGDIR = "%s/cfg" % self.BASEDIR
        self.CODEDIR = self._j.core.myenv.config["DIR_CODE"]
        self.HOMEDIR = self._j.core.myenv.config["DIR_HOME"]
        self.TEMPLATEDIR = "%s/templates" % self.VARDIR
        self.BINDIR = "%s/bin" % self.BASEDIR
        self.LOGDIR = "%s/log" % self.VARDIR

    def __str__(self):
        out = ""
        for key, value in self.__dict__.items():
            if key[0] == "_":
                continue
            out += "%-20s : %s\n" % (key, value)
        out = self._j.core.text.sort(out)
        return out

    __repr__ = __str__
