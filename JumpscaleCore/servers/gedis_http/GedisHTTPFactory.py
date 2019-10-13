from Jumpscale import j
import traceback
from bottle import post, run, response, request, Bottle

app = Bottle()
"""
~> curl -i -XPOST localhost:8903/actors/blog/get_metadata --data '{"args":{"blog":"xmon"}}' -H "Content-Type: application/json"
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 376
Date: Thu, 12 Sep 2019 16:01:13 GMT

{"blog_name": "xmon", "blog_title": "xmonader weblog", "blog_description": "let there be posts", "author_name": "ahmed", "author_email": "ahmed@there.com", "author_image_filename": "", "base_url": "", "url": "", "posts_dir": "/sandbox/code/gitlab/xmonader/sample-blog-jsx/posts", "github_username": "xmonader", "github_repo_url": "git@gitlab.com:xmonader/sample-blog-jsx.git"}3BOTDEVEL:3bot:~: 

~> curl -XPOST localhost:8903/actors/blog/get_tags
["python", "lame", "markdown", "java"]3BOTDEVEL:3bot:~: 

"""


def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS"
        response.headers[
            "Access-Control-Allow-Headers"
        ] = "Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token"

        if request.method != "OPTIONS":
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors


@app.route("/<name>/<cmd>", method="post")
@enable_cors
def client_handler(name, cmd):
    client = j.clients.gedis.get(name="main_gedis_threebot", port=8901)
    actor = getattr(client.actors, name, None)
    if not actor:
        response.status = 404
        return f"Actor {name} does not exist"
    command = getattr(actor, cmd, None)
    if not command:
        response.status = 400
        return f"Actor {name} does not have command {cmd}"
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


class GedisHTTPFactory(j.baseclasses.object, j.baseclasses.testtools):

    __jslocation__ = "j.servers.gedishttp"

    def get_app(self):
        return app
