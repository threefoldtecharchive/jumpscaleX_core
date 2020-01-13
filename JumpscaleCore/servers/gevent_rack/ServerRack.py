from Jumpscale import j
from Jumpscale.servers.gedis_http.GedisHTTPFactory import enable_cors

# from .ScheduledJob import ScheduledJob
from .ScheduledRun import ScheduledRun
import sys
import mimetypes


from gevent import monkey

monkey.patch_all(subprocess=False)
import gevent
from gevent import event

# from gevent import Greenlet


class StripPathMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, e, h):
        e["PATH_INFO"] = e["PATH_INFO"].rstrip("/")
        return self.app(e, h)


class ServerRack(j.baseclasses.object):
    """
    is a group of gedis servers in a virtual rack
    """

    def _init(self, **kwargs):
        self.servers = {}
        self.schedulers = {}
        self._logger_enable()
        self.is_started = False

    def add(self, name, server):
        """add a gevent server

        if the server rack is already started it will start the added server too otherwise it will only add it
        REMARK: make sure that subprocesses are run before adding gevent servers

        :param name: server name
        :type name: str
        :param server: gevent server
        :type server: gevent.baseserver.BaseServer
        """
        assert server

        if self.is_started and not name in self.servers:
            self.servers[name] = server
            server.start()
        else:
            self.servers[name] = server

    def scheduler_get(self, name, timeout=0):
        """

        :param self:
        :param name:
        :param timeout: in seconds after start
        :return:
        """
        if name in self.schedulers:
            raise j.exceptions.Input("cannot add scheduler with name:%s" % name)
        self.schedulers[name] = ScheduledRun(name=name, timeout=timeout)
        return self.schedulers[name]

    def bottle_server_add(
        self, name="bottle", port=4442, app=None, websocket=False, force_override=False, strip_slash=True
    ):
        """add a bottle app server

        :param name: name, defaults to "bottle"
        :type name: str, optional
        :param port: port to listen on, defaults to 4442
        :type port: int, optional
        :param app: app, if not given, will be created, defaults to None
        :type app: WSGI application, optional
        :param websocket: enable websocket handler, defaults to False
        :type websocket: bool, optional
        :param force_override: if set, the app will be re-added, defaults to False
        :type force_override: bool, optional
        :param strip_slash: strip slash for all routes, so e.g `/index/` will match `/index` too, defaults to True
        :type strip_slash: bool, optional
        """
        # TODO: improve the check for name+port combo
        if name in self.servers and not force_override:
            return True

        from gevent.pywsgi import WSGIServer
        from geventwebsocket.handler import WebSocketHandler

        if not app:

            from bottle import route, template, request, Bottle, abort, template, response

            app = Bottle()

            @app.route("/<url:re:.+>")
            @enable_cors
            def index(url):
                try:
                    file = j.sal.bcdbfs.file_read("/" + url)
                except j.exceptions.NotFound:
                    abort(404)
                response.headers["Content-Type"] = mimetypes.guess_type(url)[0]
                return file

        if strip_slash:
            app = StripPathMiddleware(app)

        if not websocket:
            server = WSGIServer(("0.0.0.0", port), app)
        else:
            server = WSGIServer(("0.0.0.0", port), app, handler_class=WebSocketHandler)

        self.add(name=name, server=server)

    def _get_cert(self):
        # FIXME: sometimes returns incorrect values (in the first request)
        certs_path = "/etc/resty-auto-ssl/letsencrypt/certs/"

        while True:
            domains = j.sal.fs.listDirsInDir(certs_path)
            if domains:
                domain = domains[0]
                ssl_keyfile = j.sal.fs.joinPaths(domain, "privkey.pem")
                ssl_certfile = j.sal.fs.joinPaths(domain, "cert.pem")
                break
            else:
                gevent.sleep(1)

        return ssl_keyfile, ssl_certfile

    def webdav_server_add(self, name="webdav", path="/tmp", port=4443, webdavprovider=None, user_mapping={}):
        """
        to test manually: wsgidav --root . --server gevent -p 8888 -H 0.0.0.0 --auth anonymous
        don't forget to install first using: kosmos 'j.servers.rack._server_test_start()'

        can use cyberduck to test

        to implement custom backend: https://github.com/mar10/wsgidav/blob/master/wsgidav/samples/virtual_dav_provider.py

        :param name:
        :param path:
        :param port:
        :param webdavprovider:
        :return:
        """

        # from wsgidav.version import __version__
        # from wsgidav.wsgidav_app import DEFAULT_CONFIG, WsgiDAVApp
        from wsgidav.wsgidav_app import WsgiDAVApp
        from gevent.pywsgi import WSGIServer

        if not webdavprovider:
            from wsgidav.fs_dav_provider import FilesystemProvider

            webdavprovider = FilesystemProvider(path)

        def addUser(realmName, user, password, description, roles=[]):
            realmName = "/" + realmName.strip(r"\/")
            userDict = user_mapping.setdefault(realmName, {}).setdefault(user, {})
            userDict["password"] = password
            userDict["description"] = description
            userDict["roles"] = roles

        if user_mapping == {}:
            addUser("", "root", "root", "")

        config = {
            "host": "0.0.0.0",
            "port": port,
            "provider_mapping": {"/": webdavprovider},
            "verbose": 1,
            "simple_dc": {"user_mapping": user_mapping},
        }

        app = WsgiDAVApp(config)
        server = WSGIServer(("0.0.0.0", port), application=app)

        self.add(name=name, server=server)

    def websocket_server_add(self, name="websocket", port=4444, appclass=None):

        from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
        from collections import OrderedDict

        if not appclass:

            class EchoApplication(WebSocketApplication):
                def on_open(self):
                    print("Connection opened")

                def on_message(self, message):
                    self.ws.send(message)

                def on_close(self, reason):
                    print(reason)

            appclass = EchoApplication

        server = WebSocketServer(("0.0.0.0", port), Resource(OrderedDict([("/", appclass)])))

        self.add(name=name, server=server)

    def websocket_bottle_server_add(self, name="websocket", port=4444, appclass=None):

        from bottle import request, Bottle, abort

        app = Bottle()

        @app.route("/websocket")
        def handle_websocket():
            wsock = request.environ.get("wsgi.websocket")
            if not wsock:
                abort(400, "Expected WebSocket request.")

            while True:
                try:
                    message = wsock.receive()
                    wsock.send("Your message was: %r" % message)
                except WebSocketError:
                    break

        from gevent.pywsgi import WSGIServer
        from geventwebsocket import WebSocketError
        from geventwebsocket.handler import WebSocketHandler

        server = WSGIServer(("0.0.0.0", port), app, handler_class=WebSocketHandler)

        self.add(name=name, server=server)

    def start(self, wait=True):
        # started = []
        keys = [key for key in self.servers.keys()]
        try:
            for key in keys:
                if key in self.servers:
                    server = self.servers[key]
                    try:
                        server.start()
                    except Exception as e:
                        j.shell()
                        w
                    # started.append(server)
                    name = getattr(server, "name", None) or server.__class__.__name__ or "Server"
                    self._log_info("%s started on %s" % (name, server.address))
            self.is_started = True

        except:
            self.stop()
            self.is_started = False
            raise

        if wait:
            forever = event.Event()
            try:
                forever.wait()
            except KeyboardInterrupt:
                self.stop()

    def stop(self, servers=None):
        self._log_info("stopping server rack")
        if servers is None:
            servers = self.servers.values()
        for server in servers:
            try:
                server.stop()
            except:
                if hasattr(server, "loop"):  # gevent >= 1.0
                    server.loop.handle_error(server.stop, *sys.exc_info())
                else:  # gevent <= 0.13
                    import traceback

                    traceback.print_exc()
