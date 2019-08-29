from Jumpscale import j
from .GeventGunServer import GeventGunServer
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from collections import OrderedDict

JSBASE = j.baseclasses.object


class GundbFactory(JSBASE):

    __jslocation__ = "j.servers.gundb"

    def _init(self, **kwargs):
        self._logger_enable()

    def gevent_server_get(self, port=7766):

        """
        returns a gevent server for j.servers.rack

        """
        server = WebSocketServer(("", port), Resource(OrderedDict([("/", GeventGunServer)])))
        return server

    def install(self):
        """
        kosmos 'j.servers.gundb.install()'

        :return:
        """
        # if install requirements put them here
        j.builders.runtimes.python3.pip_package_install("websockets")

    def _server_test_start(self, background=False):
        """
        kosmos 'j.servers.gundb._server_test_start()'

        :param manual means the server is run manually using e.g. kosmos 'j.servers.rack.start(background=True)'

        """

        if not background:

            self.install()

            rack = j.servers.rack.get()

            from bottle import route, template, request, Bottle, abort, template, static_file

            app = Bottle()

            # @app.route("/")
            # def index():
            #     return "<b>Hello World</b>!"

            @app.route("/")
            def todo():
                return static_file("todo.html", root="%s/html" % self._dirpath)

            @app.route("/<path:path>")
            def static(path):
                return static_file(path, root="%s/html" % self._dirpath)

            @app.route("/hello/<name>")
            def hello(name):
                return template("<b>Hello {{name}}</b>!", name=name)

            @app.route("/stream")
            def stream():
                yield "START"
                yield "MIDDLE"
                yield "END"

            # add a bottle webserver to it
            rack.bottle_server_add(name="bottle", port=7767, app=app)

            # add gundb server to it
            gundb_server = self.gevent_server_get()
            rack.add("gunserver", gundb_server)

            rack.start()

        else:

            S = """
            from gevent import monkey
            monkey.patch_all(subprocess=False)
            from Jumpscale import j
            
            #start the gundb server using gevent rack
            j.servers.gundb._server_test_start()
                        
            """

            S = j.core.tools.text_replace(S, args)

            s = j.servers.startupcmd.new(name="gundb_test")
            s.cmd_start = S
            # the MONKEY PATCH STATEMENT IS A WEIRD ONE, will make sure that before starting monkeypatching will be done
            s.executor = "tmux"
            s.interpreter = "python"
            s.timeout = 10
            s.ports = 7766
            if not s.is_running():
                s.stop()
            s.start()

    def test(self):
        """
        kosmos 'j.servers.gundb.test()'

        """

        self._server_test_start(background=True)
        j.shell()

        print("tests are ok")
