from Jumpscale import j
import requests
from urllib.parse import urlencode


class Oauth2ProviderClient(j.baseclasses.object_config):
    _SCHEMATEXT = """
    @url = jumpscale.oauth2_provider.client
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
        return response.json()

    def authorize(self, code, state):
        access_token_data = self.get_access_token(code, state)
        if "access_token" not in access_token_data:
            raise j.exceptions.Value("User is not authorized")

        access_token = access_token_data.get("access_token")
        self.session.headers["Authorization"] = f"bearer {access_token}"

        response = self.session.get(self.user_info_url)
        response.raise_for_status()
        data = response.json()

        userinfo = {}
        for field in self.user_info_fields:
            userinfo[field] = data.get(field, None)
        return userinfo
