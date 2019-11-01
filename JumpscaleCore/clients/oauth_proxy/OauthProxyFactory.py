from Jumpscale import j
from .OauthProxyClient import OauthProxyClient

JSConfigBase = j.baseclasses.object_config_collection


class OauthProxyFactory(j.baseclasses.object_config_collection):
    __jslocation__ = "j.clients.oauth_proxy"
    _CHILDCLASS = OauthProxyClient
