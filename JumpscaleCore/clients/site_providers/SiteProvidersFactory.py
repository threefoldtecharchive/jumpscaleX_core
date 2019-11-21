from Jumpscale import j
from .SiteProvidersClient import SiteProvidersClient

JSConfigBase = j.baseclasses.object_config_collection


class SiteProvidersFactory(j.baseclasses.object_config_collection):
    __jslocation__ = "j.clients.site_providers"
    _CHILDCLASS = SiteProvidersClient
