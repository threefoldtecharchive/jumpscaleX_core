from Jumpscale import j
from .JSBase import JSBase

from .JSBase import JSBase


class ThreeBotActorBase(JSBase):
    def _init_actor(self, **kwargs):
        self._schemas = {}
        if "gedis_server" in kwargs:
            self._gedis_server = kwargs["gedis_server"]
            self._threebot_server = self._gedis_server._threebot_server
            if self._threebot_server:
                self._bcdb_get = self._threebot_server.bcdb_get
                self._rack_server = self._threebot_server._rack_server

        self._scheduler = None

    @property
    def scheduler(self):
        if not self._scheduler:
            name = self._name
            self._scheduler = j.servers.rack.current.scheduler_get(name, timeout=0)
        return self._scheduler
