from Jumpscale import j
from .OauthProviderClient import OauthProviderClient

JSConfigBase = j.baseclasses.object_config_collection


class OauthProviderFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.oauth_provider"
    _CHILDCLASS = OauthProviderClient
