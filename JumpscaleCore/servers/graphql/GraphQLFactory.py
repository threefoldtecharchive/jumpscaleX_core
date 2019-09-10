from Jumpscale import j

JSBASE = j.baseclasses.object


class GraphQLFactory(JSBASE):

    __jslocation__ = "j.servers.graphql"
    _SCHEMA_TEXT = """
        @url = graphql.posts.schema
        info_id** =  (I)
        title = (S) 
        author = (S)
        name = (S)
        """

    def _init(self, **kwargs):
        self._logger_enable()

    @property
    def ip(self):
        if not hasattr(self, "_ip"):
            import socket

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._ip = s.getsockname()[0]
        return self._ip

    def install(self):
        """
        kosmos 'j.servers.gundb.install()'

        :return:
        """
        j.builders.runtimes.python3.pip_package_install("bottle")
        j.builders.runtimes.python3.pip_package_install("graphene==2.1.7")
        j.builders.runtimes.python3.pip_package_install("flake8")
        j.builders.runtimes.python3.pip_package_install("tox")
        j.builders.runtimes.python3.pip_package_install("graphql-ws")
        j.builders.runtimes.python3.pip_package_install("Rx==1.6.0")
        j.builders.runtimes.python3.pip_package_install("graphql_core<3.0.0a2")

    def _server_test_start(self, background=False):
        """
        kosmos 'j.servers.graphql._server_test_start()'

        :param manual means the server is run manually using e.g. kosmos 'j.servers.rack.start(background=True)'

        """

        if not background:

            self.install()

            rack = j.servers.rack.get()

            from bottle import request, Bottle, abort, static_file, template
            from .GraphqlBottle import graphql_middleware
            from geventwebsocket import WebSocketError
            from .schema import schema
            from graphql_ws.gevent import GeventSubscriptionServer

            app = Bottle()

            # expose graphql end point
            graphql_middleware(app, "/graphql", schema)

            # expose graphiql
            @app.route("/graphiql")
            def graphiql():
                return static_file("graphiql.html", root="%s/html" % self._dirpath)

            # simple test, making sure websocket protocol is running
            @app.route("/websocket")
            def websockets():
                return template(
                    """
                <!DOCTYPE html>
                <html>
                <head>
                  <script type="text/javascript">
                    var ws = new WebSocket("ws://{{ip}}:7778/websockets");
                    ws.onopen = function() {
                        ws.send("Hello, world");
                    };
                    ws.onmessage = function (evt) {
                        alert(evt.data);
                    };
                  </script>
                </head>
                </html>
                """,
                    ip=self.ip,
                )

            # expose posts example
            # add post from simple for to save in bcdb
            @app.route("/posts", method="GET")
            @app.route("/posts", method="POST")
            def posts():
                model_objects = None
                if request.method == "POST":
                    data = self.parse_data(request.body)
                    # Create a model with the data and save the model for later retrieval
                    model = j.application.bcdb_system.model_get(schema=self._SCHEMA_TEXT)
                    model_objects = model.new()
                    model_objects.info_id = data["id"]
                    model_objects.title = data["title"]
                    model_objects.name = data["name"]
                    model_objects.author = data["author"]
                    model_objects.save()

                with open(self._dirpath + "/html/posts.html") as s:
                    return s.read().replace("{ip_address}", self.ip)

            # test graphql subscriptions
            @app.route("/counter")
            def counter():
                with open(self._dirpath + "/html/counter.html") as s:
                    return s.read().replace("{ip_address}", self.ip)

            # websockets app
            websockets_app = Bottle()
            subscription_server = GeventSubscriptionServer(schema)
            websockets_app.app_protocol = lambda environ_path_info: "graphql-ws"

            @websockets_app.route("/subscriptions")
            def echo_socket():
                wsock = request.environ.get("wsgi.websocket")
                if not wsock:
                    abort(400, "Expected WebSocket request.")

                subscription_server.handle(wsock)
                return []

            @websockets_app.route("/websockets")
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

            # svelete apollo graphql APP

            # -- START -- #
            @app.route("/svelte")
            def svelte():
                return static_file("index.html", root="%s/html/svelte-apollo/public" % self._dirpath)

            @app.route("/<name>")
            def serve_static(name):
                if name in ["global.css", "bundle.css", "bundle.js", "bundle.js.map", "bundle.css.map", "favicon.png"]:
                    return static_file(name, root="%s/html/svelte-apollo/public" % self._dirpath)
                abort(404)

            # -- END -- #

            # add a bottle webserver to it
            rack.bottle_server_add(name="graphql", port=7777, app=app)
            rack.bottle_server_add(name="graphql_subscriptions", port=7778, app=websockets_app, websocket=True)
            rack.start()

        else:

            S = """
            . /sandbox/env.sh;
            kosmos 'j.servers.graphql._server_test_start()'
            """

            j.servers.tmux.execute(S)

    # parse data from the form in the request body
    def parse_data(self, raw_data):
        byte_str = raw_data.read()
        raw_data = byte_str.decode("utf-8")
        out_data = {}
        temp = raw_data.split("&")
        for item in temp:
            info = item.split("=")
            out_data[info[0]] = info[1]
        return out_data

    def test(self):
        """
        kosmos 'j.servers.gundb.test()'

        """

        self._server_test_start(background=True)

        print("tests are ok")
