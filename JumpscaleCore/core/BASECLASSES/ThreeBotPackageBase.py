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


class ThreeBotPackageBase(JSBase):
    def _init_pre2(self, **kwargs):

        assert "package" in kwargs
        self._package = kwargs["package"]
        self.package_root = self._package.path
        self.gedis_server = self._package.gedis_server
        self.rack_server = self._package.threebot_server.rack_server
        self.openresty = self._package.openresty
        self.threebot_server = self._package.threebot_server
        self.actors_namespace = "default"

    @property
    def bcdb(self):
        # return system by default
        return j.data.bcdb.system

    def prepare(self):
        """
        is called at install time
        :return:
        """
        pass

    def upgrade(self):
        """
        used to upgrade
        """
        return self.prepare()

    def start(self):
        """
        called when the 3bot starts
        :return:
        """
        models_path = self.package_root + "/models"
        if j.sal.fs.exists(models_path):
            self.bcdb.models_add(path=models_path)

        actors_path = self.package_root + "/actors"
        if j.sal.fs.exists(actors_path):
            self.gedis_server.actors_add(actors_path, namespace="default")

        chatflows_path = self.package_root + "/chatflows"
        if j.sal.fs.exists(chatflows_path):
            self.gedis_server.chatbot.chatflows_load(chatflows_path)

        # FIXME or should it be removed? it'll only work if u call package.start manually.
        # def load_wiki(path=None, name=None):
        #     wiki = j.tools.markdowndocs.load(path=path, name=name, pull=False)
        #     wiki.write()

        # path = self.package_root + "/wiki"
        # if j.sal.fs.exists(path):
        #     j.servers.myjobs.workers_tmux_start(nr_workers=1)
        #     name = self._package.name
        #     job = j.servers.myjobs.schedule(load_wiki, name=name, path=path)
        #     j.servers.myjobs.wait([job.id], timeout=None, die=False)

    def stop(self):
        """
        called when the 3bot stops
        :return:
        """
        pass

    def uninstall(self):
        """
        called when the package is no longer needed and will be removed from the threebot
        :return:
        """
        # TODO: clean up bcdb ?
        pass
