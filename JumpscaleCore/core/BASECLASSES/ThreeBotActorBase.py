from Jumpscale import j
from .JSBase import JSBase


class ThreeBotActorBase(JSBase):
    def _init_actor(self, **kwargs):
        self._scheduler = None
        self._schemas = {}
        assert "package" in kwargs
        self.package = kwargs["package"]
        self.bcdb = self.package.bcdb
        self.package_author = self.package._package_author

    @property
    def scheduler(self):
        if not self._scheduler:
            name = self._name
            self._scheduler = j.servers.rack.current.scheduler_get(name, timeout=0)
        return self._scheduler
