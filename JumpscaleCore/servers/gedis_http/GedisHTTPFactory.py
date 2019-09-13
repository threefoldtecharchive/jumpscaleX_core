from Jumpscale import j

from bottle import post, run, response, request, Bottle

app = Bottle()
"""
~> curl -i -XPOST localhost:9201/actors/blog/get_metadata --data '{"args":{"blog":"xmon"}}' -H "Content-Type: application/json"
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 376
Date: Thu, 12 Sep 2019 16:01:13 GMT

{"blog_name": "xmon", "blog_title": "xmonader weblog", "blog_description": "let there be posts", "author_name": "ahmed", "author_email": "ahmed@there.com", "author_image_filename": "", "base_url": "", "url": "", "posts_dir": "/sandbox/code/gitlab/xmonader/sample-blog-jsx/posts", "github_username": "xmonader", "github_repo_url": "git@gitlab.com:xmonader/sample-blog-jsx.git"}3BOTDEVEL:3bot:~: 

~> curl -XPOST localhost:9201/actors/blog/get_tags
["python", "lame", "markdown", "java"]3BOTDEVEL:3bot:~: 

"""


@app.route("/actors/<name>/<cmd>", method="post")
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
    result = command(**data["args"])
    if content_type:
        result = getattr(result, f"_{content_type}", result)
    return result


class GedisHTTPFactory(j.baseclasses.object, j.baseclasses.testtools):

    __jslocation__ = "j.servers.gedishttp"

    def get_app(self):
        return app
