from Jumpscale import j
from bottle import Bottle, request, response

app = Bottle()

client = j.clients.oauth_proxy.get("main")
oauth_app = j.tools.oauth_proxy.get(app, client)


@app.route("/oauth/authorize")
def authorize():
    return oauth_app.authorize()


@app.route("/oauth/callback")
def callback():
    return oauth_app.oauth_callback()


@app.route("/oauth/providers")
def providers():
    response.content_type = "application/json"
    return j.data.serializers.json.dumps(client.providers_list())


@app.route("/oauth/key")
def key():
    return j.data.nacl.default.verify_key_hex


app = oauth_app.app


class Oauth2Factory(j.baseclasses.threebot_factory):
    __jslocation__ = "j.threebot_factories.package.oauth2"

    def get_app(self):
        return app
