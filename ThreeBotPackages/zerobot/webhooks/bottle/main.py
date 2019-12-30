import hmac

from bottle import abort, response, request, Bottle, redirect
from hashlib import sha1

from Jumpscale import j

app = Bottle()

# NOT NICE, we don't use config manager here
SECRET = j.core.tools.text_replace("{DIR_BASE}/var/github_webhook_secret")


@app.route("/webhook/github", method="post")
def webhook_github():
    event = request.headers.get("X-GitHub-Event")
    if event != "push":
        abort(406, f"Wrong even type: {event}")

    content_type = request.headers.get("Content-Type")
    if content_type != "application/x-www-form-urlencoded":
        abort(406, f"wrong content type header: {content_type}")

    signature = request.headers.get("X-Hub-Signature")
    if not signature:
        abort(400, "No signature header found")

    webhook_secret = j.sal.fs.readFile(SECRET, binary=True).rstrip()
    hexdigest = hmac.new(webhook_secret, request.body.read(), sha1).hexdigest()
    hashed_body = f"sha1={hexdigest}"

    if not hmac.compare_digest(signature, hashed_body):
        abort(401, "Invalid secret")

    payload = j.data.serializers.json.loads(request.params.payload)
    j.clients.git.pullGitRepo(payload["repository"]["ssh_url"])


class WebhooksFactory(j.baseclasses.threebot_factory):
    __jslocation__ = "j.threebot_factories.package.webhooks"

    def get_app(self):
        return app
