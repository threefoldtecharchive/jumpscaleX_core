from Jumpscale import j
import requests
from urllib.parse import urlencode


class OauthProviderClient(j.baseclasses.object_config):
    _SCHEMATEXT = """
    @url = jumpscale.oauth_provider.client
    name** = "main" (S)
    client_id = "" (S)
    client_secret = "" (S)
    access_token_url = "" (S)
    authorize_url = "" (S)
    redirect_url = "" (S)
    user_info_url = "" (S)
    scope = "" (S)
    user_info_fields = "username,email" (LS)
    """

    def _init(self, **kwargs):
        self.session = requests.Session()

    def get_authorization_url(self, state):
        params = dict(response_type="code", client_id=self.client_id, redirect_url=self.redirect_url, state=state)

        if self.scope:
            params["scope"] = self.scope

        url = "{authorize_url}?{params}".format(authorize_url=self.authorize_url, params=urlencode(params))
        return url

    def get_access_token(self, code, state):
        params = dict(
            grant_type="authorization_code",
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_url=self.redirect_url,
            code=code,
            state=state,
        )
        headers = {"Accept": "application/json"}
        response = requests.post(self.access_token_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()["access_token"]

    def get_user_info(self, access_token):
        self.session.headers["Authorization"] = f"bearer {access_token}"
        response = self.session.get(self.user_info_url)
        response.raise_for_status()
        data = {k: v for k, v in response.json().items() if (k in self.user_info_fields and v)}
        return data
