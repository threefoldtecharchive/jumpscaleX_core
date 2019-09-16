# from gevent import monkey
#
# monkey.patch_all(subprocess=False)

from Jumpscale import j

import gevent


# from .Community import Community
from .ServerRack import ServerRack

# from .Package import Package
import time
from gevent import event, sleep
import os
import socket
import netstr
import sys
import time

JSBASE = j.baseclasses.object


class ServerRackFactory(JSBASE):

    __jslocation__ = "j.servers.rack"

    def _init(self, **kwargs):
        self._logger_enable()
        self.current = None

    def get(self):

        """
        returns a gevent rack

        to start the server manually do:
        js_shell 'j.servers.rack.start(namespace="test", secret="1234")'

        """
        if not self.current:
            self.current = ServerRack()
        return self.current

    def install(self):
        """
        kosmos 'j.servers.rack._server_test_start()'
        :return:
        """
        j.builders.runtimes.python3.pip_package_install("bottle,webdavclient3")
        j.builders.runtimes.python3.pip_package_install("git+https://github.com/mar10/wsgidav.git")

    def _server_test_start(
        self, zdb=False, background=False, gedis=True, webdav=True, bottle=True, websockets=True, gedis_ssl=False
    ):
        """
        kosmos 'j.servers.rack._server_test_start()'

        :param manual means the server is run manually using e.g. kosmos 'j.servers.rack.start(background=True)'

        """

        if not background:

            self.install()

            if zdb:
                j.servers.zdb.test_instance_start(destroydata=True)
                admin_zdb_cl = j.clients.zdb.client_admin_get(port=9901)
                cl = admin_zdb_cl.namespace_new("test", secret="1234")

            if gedis:
                gedis = j.servers.gedis.get_gevent_server("test", port=8901)

            rack = self.get()
            rack.add("gedis", gedis)

            if gedis_ssl:
                gedis_ssl = j.servers.gedis.get_gevent_server("test", ssl=True, port=8901)
                rack.add("gedis_ssl", gedis_ssl)

            if webdav:
                rack.webdav_server_add()

            if websockets:
                rack.websocket_server_add()
                # rack.websocket_bottle_server_add

            if bottle:
                rack.bottle_server_add()

            rack.start()

        else:
            ports = []
            args = {}
            if gedis:
                ports.append(8901)
                args["gedis"] = "True"
            else:
                args["gedis"] = "False"
            if gedis_ssl:
                # ports.append(8901)
                args["gedis_ssl"] = "True"
            else:
                args["gedis_ssl"] = "False"
            if webdav:
                # ports.append(4443)
                args["webdav"] = "True"
            else:
                args["webdav"] = "False"
            if bottle:
                # ports.append(4442)
                args["bottle"] = "True"
            else:
                args["bottle"] = "False"
            if websockets:
                # ports.append(4444)
                args["websockets"] = "True"
            else:
                args["websockets"] = "False"

            S = """
            from gevent import monkey
            monkey.patch_all(subprocess=False)
            from Jumpscale import j
            j.servers.rack._server_test_start(gedis={gedis},gedis_ssl={gedis_ssl},webdav={webdav}, bottle={bottle}, websockets={websockets})
            """

            S = j.core.tools.text_replace(S, args)

            s = j.servers.startupcmd.get(name="gedis_test")
            s.cmd_start = S
            # the MONKEY PATCH STATEMENT IS A WEIRD ONE, will make sure that before starting monkeypatching will be done
            s.executor = "tmux"
            s.interpreter = "python"
            s.timeout = 10
            s.ports = ports
            if not s.is_running():
                s.stop()
            s.start()

    def test(self, start=True, gedis=True, gedis_ssl=False, webdav=False, bottle=True, websockets=False):
        """
        kosmos 'j.servers.rack.test()'
        kosmos 'j.servers.rack.test(gedis_ssl=True)'
        kosmos 'j.servers.rack.test(ssl=False)'
        kosmos 'j.servers.rack.test(start=True)'

        :param manual means the server is run manually using e.g. js_shell 'j.servers.rack.start()'

        """

        if start:
            self._server_test_start(
                background=True, gedis=gedis, gedis_ssl=gedis_ssl, webdav=webdav, bottle=bottle, websockets=websockets
            )

        namespace = "system"
        secret = "1234"
        cl = j.clients.gedis.new(namespace, namespace=namespace, port=8901, secret=secret, host="localhost")
        assert cl.ping()
        cl.actors
        assert cl.actors.system.ping() == b"PONG"

        if gedis_ssl:
            cl2 = j.clients.gedis.new(
                namespace, namespace=namespace, port=8901, secret=secret, host="localhost", ssl=True
            )
            assert cl2.ping()
            cl.actors
            assert cl.actors.system.ping() == b"PONG"

        if webdav:
            # how to use see https://github.com/ezhov-evgeny/webdav-client-python-3/blob/da46592c6f1cc9fb810ca54019763b1e7dce4583/webdav3/client.py#L197
            options = {"webdav_hostname": "http://127.0.0.1:4443", "webdav_login": "root", "webdav_password": "root"}
            from webdav3.client import Client

            cl = Client(options)
            cl.check()
            assert len(cl.list("")) > 0

        if websockets:
            # TODO: does not work yet
            from websocket import create_connection

            ws = create_connection("ws://localhost:4444")
            ws.send("Hello, World")
            result = ws.recv()
            print(result)
            # ws.close()

        if bottle:
            import requests

            # https://realpython.com/python-requests/#the-get-request

            r1 = requests.get("http://localhost:4442/")
            self._log(r1.status_code)
            self._log(r1.content)
            assert r1.content == b"<b>Hello World</b>!"
            assert r1.status_code == 200
            self._log_info("hello kds")
            r2 = requests.get("http://localhost:4442/hello/kds")
            assert r2.status_code == 200
            self._log(r2.status_code)
            self._log_info("stream")
            r3 = requests.get("http://localhost:4442/stream")
            assert r3.status_code == 200
            self._log(r3.status_code)
            self._log(r3.content)

        print("tests are ok")
