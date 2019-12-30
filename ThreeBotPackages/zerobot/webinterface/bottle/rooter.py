from bottle import Bottle, abort, post, request, response, run
from Jumpscale import j
from jinja2 import Environment, FileSystemLoader, select_autoescape
import bottle

try:
    from beaker.middleware import SessionMiddleware
except (ModuleNotFoundError, ImportError):
    j.builders.runtimes.python3.pip_package_install("beaker")
    from beaker.middleware import SessionMiddleware


app = Bottle()

# to check beaker session
session_opts = {"session.type": "file", "session.data_dir": "./data", "session.auto": True}
app_with_session = SessionMiddleware(app, session_opts)

templates_path = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), "..", "templates")
env = Environment(loader=FileSystemLoader(templates_path), autoescape=select_autoescape(["html", "xml"]))


def get_ws_url():
    """get the proper ws url from the request"""
    url_parts = request.urlparts
    ws_scheme = "ws"
    if url_parts.scheme == "https" or request.headers["x-forwarded-proto"] == "https":
        ws_scheme = "wss"

    ws_url = f"{ws_scheme}://{url_parts.hostname}"
    if url_parts.port:
        ws_url = f"{ws_url}:{url_parts.port}"
    return ws_url


from .chat import *
from .gedis import *
from .wiki import *
