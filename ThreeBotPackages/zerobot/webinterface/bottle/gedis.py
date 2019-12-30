import json
import mimetypes
import traceback

from bottle import Bottle, abort, post, request, response, run
from bottle.ext.websocket import GeventWebSocketServer, websocket
from Jumpscale import j
from Jumpscale.servers.gedis_http.GedisHTTPFactory import enable_cors

GEDIS_PORT = 8901
from .rooter import app

#######################################
###### GEDIS WEBSOCKET ROUTES #########
#######################################
@app.route("/gedis/websocket", apply=[websocket])
def gedis_websocket(ws):
    # TODO: getting a gedis client should happen only once
    client_gedis = j.clients.gedis.get("main", port=GEDIS_PORT)
    while True:
        message = ws.receive()
        if message is not None:
            data = json.loads(message)
            commands = data["command"].split(".")
            if data["command"].casefold() == "system.ping":
                ws.send(j.data.serializers.json.dumps(client_gedis.ping()))
                return
            cl = getattr(client_gedis.actors, commands[0])

            for attr in commands[1:]:
                cl = getattr(cl, attr)

            args = data.get("args", {})
            response = cl(**args)
            if isinstance(response, dict):
                ws.send(j.data.serializers.json.dumps(response))
            elif hasattr(response, "_json"):
                ws.send(j.data.serializers.json.dumps(response._ddict_hr))
            elif isinstance(response, bytes):
                ws.send(response.decode())
            elif response is None:
                ws.send("")
            else:
                ws.send(response)
        else:
            break


#######################################
######## GEDIS HTTP ROUTES ############
#######################################
def get_actor(client, name, retry=True):
    """try to get an actor from a gedis client

    will reload the client and try again if the actor is not available

    :param client: gedis client
    :type client: GedisClient
    :param name: actor name
    :type name: str
    :param retry: if set, will try to reload if actor is not found
    :type retyr: bool
    """
    actor = getattr(client.actors, name, None)
    if not actor and retry:
        client.reload()
        return get_actor(client, name, retry=False)
    return actor


@app.route("/<threebot_name>/<package_name>/actors/<name>/<cmd>", method=["post", "get", "options"])
@app.route("/gedis/http/<name>/<cmd>", method=["post", "get", "options"])
@enable_cors
def gedis_http(name, cmd, threebot_name=None, package_name=None):
    if threebot_name and package_name:
        fullname = f"{threebot_name}.{package_name}"
        client = j.clients.gedis.get(name=f"{fullname}_client", package_name=fullname, port=8901)
    else:
        client = j.clients.gedis.get()

    actor = get_actor(client, name)
    if not actor:
        response.status = 404
        return f"Actor {name} does not exist"
    command = getattr(actor, cmd, None)
    if not command:
        response.status = 400
        return f"Actor {name} does not have command {cmd}"

    if request.method == "GET":
        params = dict(request.params)
        data = {"args": params}
    else:
        data = request.json or {"args": {}}
    content_type = data.get("content_type", "json")
    if content_type not in ["json", "msgpack"]:
        response.status = 400
        return f"content_type needs to be either json or msgpack"
    response.headers["Content-Type"] = f"application/{content_type}"
    try:

        result = command(**data["args"])
    except Exception as ex:
        err = "".join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))
        response.status = 400
        result = {"error": err}
        if content_type == "json":
            result = j.data.serializers.json.dumps(result)
        else:  # msgpack
            result = j.data.serializers.msgpack.dumps(result)
    else:
        if content_type:
            result = getattr(result, f"_{content_type}", result)
    return result


@app.route("/bcdbfs/<url:re:.+>")
@enable_cors
def index(url):
    try:
        file = j.sal.bcdbfs.file_read("/" + url)
    except j.exceptions.NotFound:
        abort(404)
    response.headers["Content-Type"] = mimetypes.guess_type(url)[0]
    return file
