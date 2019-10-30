from Jumpscale import j
from urllib.parse import urlencode


class Oauth2ProxyrClient(j.baseclasses.object_config):
    _SCHEMATEXT = """
    @url = jumpscale.site_providers.client
    name** = "main" (S)
    url = "" (S)
    callback_url = "" (S)
    providers = (LS)
    """

    def provider_list(self):
        return list(self.providers.keys())

    def provider_register(self, name):
        if not j.clients.oauth2_provider.exists(name):
            raise j.exceptions.Value("Provider {} is not found".format(name))

        self.providers.append(name)

    def provider_delete(self, name):
        try:
            self.providers.remove(name)
        except ValueError:
            raise j.exceptions.Value("Provider {} is not registered".format(name))

    def login(self, session, provider_name):
        if provider_name not in self.providers:
            raise j.exceptions.Value("Provider {} is not found".format(provider_name))

        provider = j.clients.oauth2_provider.get(name=provider_name)
        url, state = provider.authorization_url
        session["uid"] = state
        return url

    def callback_handler(self, session, code, state):
        uid = session.get("uid")
        provider_name = session.get("provider")
        redirect_url = session.get("redirect_url")

        if not provider_name:
            raise j.exceptions.NotFound("Couldn't find provider in session")

        if state != uid:
            raise j.exceptions.Value("Invalid state")

        provider = j.clients.oauth2_provider.get(name=provider_name)
        userinfo = provider.authorize(code, state)

        params = {"uid", uid}
        params.update(**userinfo)
        params_str = urlencode(params)
        rurl = "{redirect_url}?{params}".format(redirect_url=redirect_url, params=params_str)
        return rurl
