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


from Jumpscale import j
from .JSBase import JSBase
from .TestTools import TestTools
import os


class PackageInstaller:
    pass


class ThreeBotFactoryBase(JSBase, TestTools):
    def client_get(self):
        """
        """
        self.client = j.servers.threebot.start()

        return self.client

    @property
    def packagename(self):
        path = self._dirpath
        path = path.rstrip("/")
        splitted = path.split("/")
        u = splitted.index("ThreeBotPackages")
        name = "__".join(splitted[u + 1 :])
        return name

    def _connect(self):
        print("CONNECT")
        if self.packagename in j.threebot.packages.__dict__:
            return
        if j.tools.threebot_packages.exists(self.packagename):
            p = j.tools.threebot_packages.get(self.packagename)
            p.start()
            j.threebot.packages.__dict__[self.packagename] = p
        else:
            j.threebot.packages.__dict__[self.packagename] = PackageInstaller()
            j.threebot.packages.__dict__[self.packagename].install = self.install()

    def install(self):
        server = j.servers.threebot.default
        server.save()
        # TODO: need to call the package_manager actor on the threebot, and ask to load the package there
        # should not be done manually
        package = j.tools.threebot_packages.get(self.packagename, path=self._dirpath, threebot_server_name=server.name)
        package.prepare()
        package.save()
        self._log_info(f"{packagename} loaded")

        self._connect()

        return "OK"

    def start(self):
        # DO NOT START IN FOREGROUND
        # server = j.servers.threebot.default
        # server.start(web=self._web, ssl=self._ssl)

        # WILL GIVE YOU THE MAIN THREEBOT,STARTED THROUGH TMUX
        self.install()
        self.client = j.servers.threebot.start()
