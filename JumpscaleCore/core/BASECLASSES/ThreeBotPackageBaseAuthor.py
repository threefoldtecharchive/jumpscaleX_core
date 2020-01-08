from Jumpscale import j
from .JSBase import JSBase


class ThreeBotPackageBaseAuthor(JSBase):
    def _init_actor(self, **kwargs):

        assert "package" in kwargs
        self._package = kwargs["package"]
        self.package_root = self._package.path

        self.bcdb = self._package.bcdb

        if hasattr(j.threebot, "servers"):
            self.gedis_server = j.threebot.servers.gedis
            self.gevent_rack = j.threebot.servers.gevent_rack
            self.openresty = j.threebot.servers.web
            self.threebot_server = j.threebot.servers.core

        self.actors_namespace = self._package.actor.namespace

    ###DO NOT DO ANYTHING IN THE BASECLASSES BELOW PLEASE

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
        pass

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
        pass
