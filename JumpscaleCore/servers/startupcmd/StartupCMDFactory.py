# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


from .StartupCMD import StartupCMD

from Jumpscale import j
import time


class StartupCMDFactory(j.baseclasses.object_config_collection_testtools):

    _CHILDCLASS = StartupCMD
    __jslocation__ = "j.servers.startupcmd"

    def _init(self, **kwargs):
        tdir = j.sal.fs.joinPaths(j.sal.fs.joinPaths(j.dirs.VARDIR, "cmds"))
        j.sal.fs.createDir(tdir)

        self._cmdsdir = tdir

    def test(self, name=None):
        """
        kosmos 'j.servers.startupcmd.test()'
        :return:
        """

        j.servers.startupcmd.get("http")
        j.servers.startupcmd.get("tmuxserver")
        j.servers.startupcmd.get("http_corex")
        j.servers.startupcmd.get("http_back")

        self._test_run(name=name)

        self.http.delete()
        self.tmuxserver.delete()
        self.http_back.delete()

        print("TEST STARTUPCMDS OK")
