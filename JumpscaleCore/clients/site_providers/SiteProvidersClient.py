from Jumpscale import j


class SiteProvidersClient(j.baseclasses.object_config):
    _SCHEMATEXT = """
    @url = jumpscale.site_providers.client
    name** = "main" (S)
    providers = {} (dict)
    """

    def provider_list(self):
        return list(self.providers.keys())

    def provider_add(
        self,
        name,
        client_id,
        client_secret,
        access_token_url,
        authorize_url,
        redirect_url,
        scope,
        user_info_url,
        login_field,
    ):
        self.providers[name] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token_url": access_token_url,
            "authorize_url": authorize_url,
            "redirect_url": redirect_url,
            "scope": scope,
            "user_info_url": user_info_url,
            "login_field": login_field,
        }

    def provider_delete(self, name):
        self.providers.pop(name, None)
