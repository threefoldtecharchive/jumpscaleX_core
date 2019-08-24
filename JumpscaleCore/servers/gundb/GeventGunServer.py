import json
from Jumpscale import j
from .backend.GunUtils import *
from .backend.memory import MemoryDB
from .backend.bcdb import BCDB
from geventwebsocket import WebSocketApplication
import uuid

# import os
# import sys
# import traceback
# import redis
# import time
# from time import sleep


class App:
    def __init__(self, backend):
        self.backend = backend


app = App(BCDB())


class GeventGunServer(WebSocketApplication, j.baseclasses.object):
    def __init__(self, ws):
        WebSocketApplication.__init__(self, ws)
        j.baseclasses.object.__init__(self)

    def _init(self, **kwargs):
        self.db = MemoryDB()
        self.graph = {}  # sometimes te MemoryDB is used sometimes the graph? whats difference
        self.peers = []
        self.trackedids = []

    def _trackid(self, id_):
        """
        :param id_:
        :return:
        """
        if id_ not in self.trackedids:
            self._log_debug("CREATING NEW ID:::", id_)
            self.trackedids.append(id_)
        return id_

    # def _emit(self, data):
    #     """
    #     is that being used? TODO:
    #     :param data:
    #     :return:
    #     """
    #     resp = json.dumps(data)
    #     for p in self.peers:
    #         self._log_debug("Sending resp: ", resp, " to ", p)
    #         p.send(resp)

    def _loggraph(self, graph):
        pass
        # for soul, node in self.graph.items():
        #     self._log_debug("\nSoul: ", soul)
        #     self._log_debug("\n\t\tNode: ", node)
        #     for k, v in node.items():
        #         self._log_debug("\n\t\t{} => {}".format(k, v))

        # self._log_debug("TRACKED: ", self.trackedids, " #", len(self.trackedids))
        # self._log_debug("\n\nBACKEND: ", self.db.list())

    def on_open(self):
        print("Got client connection")

    def on_message(self, message):
        resp = {"ok": True}
        msgstr = message
        resp = {"ok": True}
        if msgstr is not None:
            msg = json.loads(msgstr)
            print("\n\n\n received {} \n\n\n".format(msg))
            if not isinstance(msg, list):
                msg = [msg]
            for payload in msg:
                # print("payload: {}\n\n".format(payload))
                if isinstance(payload, str):
                    payload = json.loads(payload)
                if "put" in payload:
                    change = payload["put"]
                    msgid = payload["#"]
                    diff = ham_mix(change, self.graph)
                    uid = self._trackid(str(uuid.uuid4()))
                    self._loggraph(self.graph)
                    # make sure to send error too in case of failed ham_mix

                    resp = {"@": msgid, "#": uid, "ok": True}
                    # print("DIFF:", diff)
                    for soul, node in diff.items():
                        for k, v in node.items():
                            if k == METADATA:
                                continue
                            self.graph[soul][k] = v
                        for k, v in node.items():
                            if k == METADATA:
                                continue
                            app.backend.put(soul, k, v, diff[soul][METADATA][STATE][k], self.graph)

                elif "get" in payload:
                    uid = self._trackid(str(uuid.uuid4()))
                    get = payload["get"]
                    msgid = payload["#"]
                    ack = lex_from_graph(get, app.backend)
                    self._loggraph(self.graph)
                    resp = {"put": ack, "@": msgid, "#": uid, "ok": True}

                self.sendall(resp)
                self.sendall(msg)

        self.ws.send(message)

    def on_close(self, reason):
        print(reason)

    def sendall(self, resp):
        for client in self.ws.handler.server.clients.values():
            client.ws.send(json.dumps(resp))
