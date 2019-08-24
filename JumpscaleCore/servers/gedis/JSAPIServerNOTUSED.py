from .handlers import WebsocketRequestHandler
from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi

# THINK IS NOT USED AT THIS POINT


class JSAPIServer:
    def __init__(self):
        self.websocket_server = pywsgi.WSGIServer(("0.0.0.0", 8001), self.websocketapp, handler_class=WebSocketHandler)

    def websocketapp(self, environ, start_response):
        if "/static/" in environ["PATH_INFO"]:
            # items = [p for p in environ['PATH_INFO'].split('/static/') if p]
            # if len(items) == 1:
            #     static_file = items[-1]
            #     if static_file in self.static_files:
            #         start_response('200 OK', [('Content-Type', 'application/javascript;charset=utf-8'),('Access-Control-Allow-Origin','*')])
            #         return [self.code_js_client]

            # file_path = j.sal.fs.joinPaths(self.static_files_path, static_file)
            # if j.sal.fs.exists(file_path):
            #     self.static_files[static_file] = j.sal.fs.readFile(file_path).replace('%%host%%', host).encode('utf-8')
            start_response(
                "200 OK",
                [("Content-Type", "application/javascript;charset=utf-8"), ("Access-Control-Allow-Origin", "*")],
            )
            code_js = self.code_js_client
            host = environ.get("HTTP_HOST")
            #
            code_js = code_js.replace("wss://", "ws://")
            code_js = code_js.replace("%%host%%", host).encode("utf-8")
            return [code_js]

            # start_response('404 NOT FOUND', [])
            # return []

        websocket = environ.get("wsgi.websocket")
        if not websocket:
            return []
        addr = "{0}:{1}".format(environ["REMOTE_ADDR"], environ["REMOTE_PORT"])
        handler = WebsocketRequestHandler(self.instance, self.cmds, self.actors, self.cmds_meta)
        handler.handle(websocket, addr)
        return []
