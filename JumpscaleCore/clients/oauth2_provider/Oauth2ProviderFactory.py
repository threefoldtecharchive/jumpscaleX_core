from Jumpscale import j
from .Oauth2ProviderClient import Oauth2ProviderClient

JSConfigBase = j.baseclasses.object_config_collection


class Oauth2ProviderFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.oauth2_provider"
    _CHILDCLASS = Oauth2ProviderClient
