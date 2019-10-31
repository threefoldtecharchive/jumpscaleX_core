from Jumpscale import j
from urllib.parse import urlencode
import requests


class OauthProxyClient(j.baseclasses.object_config):
    _SCHEMATEXT = """
    @url = jumpscale.oauth_proxy.client
    name** = "main" (S)
    url = "" (S)
    providers = (LS)
    """

    def providers_list(self):
        return list(self.providers.keys())

    def provider_add(self, name):
        self.providers.append(name)

    def provider_delete(self, name):
        try:
            self.providers.remove(name)
        except ValueError:
            raise j.exceptions.Value("Provider {} is not registered".format(name))
