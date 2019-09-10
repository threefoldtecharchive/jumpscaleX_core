import json
import asyncio
from .utils import newuid, new_node, ham_mix
from Jumpscale import j

try:
    import websockets
except:
    j.builders.runtimes.python3.pip_package_install("websockets")
    import websockets

JSConfigBase = j.baseclasses.object_config


def format_put_request(soul, **kwargs):
    ch = {"#": newuid(), "put": {soul: new_node(soul, **kwargs)}}
    return ch


def format_get_request(soul):
    ch = {"#": newuid(), "get": {"#": soul}}
    return ch


class Memory:
    def __init__(self):
        self.db = {}

    def put(self, soul, key, value, state):
        # soul -> {field:{'state':state, 'val':val, rel: relation}}
        if soul not in self.db:
            self.db[soul] = {"_": {}}
        self.db[soul][key] = value
        self.db[soul]["_"][key] = state

    def get(self, soul, key=None):
        # print("SOUL: ", soul, " KEY : ", key)
        ret = {"#": soul, "_": {"#": soul, ">": {}}}
        res = None
        if soul in self.db:
            if key and isinstance(key, str):
                res = {**ret, **self.db.get(soul)}
                return res.get(key, {})
            else:
                res = {**ret, **self.db.get(soul)}
                return res

        return ret

    def __setitem__(self, k, v):
        self.db[k] = v

    def __getitem__(self, k):
        return self.db[k]

    def list(self):
        return self.db.items()


TEMPLATE = """
addr = ""
port = 8080
base_url = "" 
user = ""
password_ = ""
"""


class GunClient(JSConfigBase):
    _SCHEMATEXT = """
        @url = jumpscale.gun.client
        name** = "" (S)
        data = "" (S)
        """

    def _init(self, **kwargs):
        if self.data is None:
            self.data = {}

        self.ws = None
        self.backend = Memory()

    @property
    def wsendpoint(self):
        return "ws://{addr}:{port}/gun".format(addr=self.config.data["addr"], port=self.config.data["port"])

    async def put(self, soul, **kwargs):
        async with websockets.connect(self.wsendpoint) as ws:
            ch = format_put_request(soul, **kwargs)
            ch_str = json.dumps(ch)
            await ws.send(ch_str)
            resp = await ws.recv()
            return resp

    async def get(self, soul, key=None):
        async with websockets.connect(self.wsendpoint) as ws:
            ch = format_get_request(soul)
            ch_str = json.dumps(ch)
            await ws.send(ch_str)
            resp = await ws.recv()
            loaded = json.loads(resp)
            change = loaded["put"]
            soul = loaded["#"]
            diff = ham_mix(change, self.backend)

            resp = {"@": soul, "#": newuid(), "ok": True}

            for soul, node in diff.items():
                for k, v in node.items():
                    if k == "_":
                        continue
                    self.backend.put(soul, k, v, diff[soul]["_"][">"][k])
            res = self.backend.get(soul, key) or "nil"
            return res
