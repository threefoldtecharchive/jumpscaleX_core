from Jumpscale import j
from .Oauth2ProxyClient import Oauth2ProxyClient

JSConfigBase = j.baseclasses.object_config_collection


class Oauth2ProxyFactory(j.baseclasses.object_config_collection):
    __jslocation__ = "j.clients.oauth2_proxy"
    _CHILDCLASS = Oauth2ProxyClient
