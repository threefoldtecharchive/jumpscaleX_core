from Jumpscale import j

from bottle import post, run, response, request, Bottle

client = j.clients.gedis.get(name='main_gedis_threebot', port=8901)
app = Bottle()

@app.route("/actors/<name>/<cmd>", method="post")
def client_handler(name, cmd):
    actor = getattr(client.actors, name, None)
    if not actor:
        response.status = 404
        return f"Actor {name} does not exist"
    command = getattr(actor, cmd, None)
    if not command:
        response.status = 400
        return f"Actor {name} does not have command {cmd}"
    data = request.json or {"args":{}}
    content_type = data.get("content_type", "json")
    if content_type not in ["json", "msgpack"]:
        response.status = 400
        return f"content_type needs to be either json or msgpack"
    response.headers['Content-Type'] = f"application/{content_type}"
    result = command(**data["args"])
    if content_type:
        result = getattr(result, f"_{content_type}", result)
    return result


class GedisHTTPFactory(j.baseclasses.object, j.baseclasses.testtools):

    __jslocation__ = "j.servers.gedishttp"

    def get_app(self):
        return app
