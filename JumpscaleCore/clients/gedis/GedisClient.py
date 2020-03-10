import binascii
import os
from io import BytesIO

import redis
from redis.connection import ConnectionError

from Jumpscale import j
from Jumpscale.servers.gedis.protocol import ProtocolHandler, Error, Disconnect
from Jumpscale.servers.gedis.secret_handshake import SHSClient

JSConfigBase = j.baseclasses.factory_data


class GedisClientActors(j.baseclasses.object):
    pass


class GedisClientSchemas(j.baseclasses.object):
    pass


class GedisClient(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.gedis.client
    name** = "main"
    host = "127.0.0.1" (S)
    port = 8901 (ipport)
    package_name = "zerobot.base" (S)  #is the full package name e.g. threebot.blog
    threebot_local_profile = "default"
    server_pk_hex = (S)
    """

    def _init(self, **kwargs):
        self._actorsmeta = {}
        if not self.package_name:
            self.package_name = "zerobot.base"
            self.save()

        assert self.package_name
        assert "." in self.package_name

        self.schemas = None
        self._actors = None
        if "package_name" in kwargs and kwargs["package_name"] and self.package_name != kwargs["package_name"]:
            raise j.exceptions.Input(
                "gedis client with name:%s was configured for other packagename:%s"
                % (self.name, kwargs["package_name"])
            )

        self._code_generated_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "gedis", self.name, "client")
        j.sal.fs.createDir(self._code_generated_dir)
        j.sal.fs.touch(j.sal.fs.joinPaths(self._code_generated_dir, "__init__.py"))

        self._client_ = None
        self._threebot_me_ = None
        self._reset()

        self._model.trigger_add(self._update_trigger)

    def _update_trigger(self, obj, action, **kwargs):
        if action in ["save", "change"]:
            self._reset()

    def _reset(self):
        self._client_ = None  # connection to server
        self._actors = None

    def ping(self):
        test = self._client.execute_command("ping")
        return test == b"PONG"

    def reload(self):
        self._log_info("reload")
        self._reset()
        assert self.ping()

        self._actorsmeta = {}
        self._actors = GedisClientActors()
        self.schemas = GedisClientSchemas()

        try:
            # this will make sure we know the core schemas as used on server
            # if system schemas not known, we get them from the server
            if not j.data.schema.exists("jumpscale_bcdb_acl_user_2"):
                r = self._client.execute_command("jsx_schemas_get")
                r2 = j.data.serializers.msgpack.loads(r)
                for key, data in r2.items():
                    schema_text, schema_url = data
                    if not j.data.schema.exists(md5=key):
                        j.data.schema.get_from_text(schema_text)

            cmds_meta = self._client.execute_command("api_meta_get", self.package_name)
        except Exception as err:
            raise j.clients.gedis._handle_error(err, redis=self._client)

        cmds_meta = j.data.serializers.msgpack.loads(cmds_meta)
        if cmds_meta["cmds"] == {}:
            return
        for key, data in cmds_meta["cmds"].items():
            actor_name = key.split(".")[-1]
            if not self.package_name or key.startswith(self.package_name):
                self._actorsmeta[actor_name] = j.servers.gedis._cmds_get(actor_name, data)

        # at this point the schema's are loaded only for the namespace identified (is all part of metadata)
        for actorname, actormeta in self._actorsmeta.items():
            tpath = "%s/templates/GedisClientGenerated.py" % (j.clients.gedis._dirpath)
            actorname_ = actormeta.namespace + "_" + actorname

            dest = j.core.tools.text_replace("{DIR_BASE}/var/codegen/gedis/%s/client/%s.py") % (self.name, actorname_)

            cl = j.tools.jinja2.code_python_render(
                obj_key="GedisClientGenerated",
                path=tpath,
                overwrite=True,
                objForHash=actorname_,
                obj=actormeta,
                dest=dest,
            )
            o = cl(client=self)
            setattr(self._actors, actorname, o)

            # get the schemas
            for schemaobj in actormeta.data.schemas:
                self._log_info("load schema: %s" % schemaobj.url)
                j.data.schema.get_from_text(schemaobj.content, url=schemaobj.url)

            self._log_info("cmds for actor:%s" % actorname)

            def process_url(url):
                url = url.replace(".", "_")
                if url.startswith("actors_"):
                    url = "_".join(url.split("_")[2:])
                return url

            for name, cmd in actormeta.cmds.items():
                if cmd.schema_in and not cmd.schema_in.url.startswith("actors."):
                    setattr(self.schemas, process_url(cmd.schema_in.url), cmd.schema_in)
                if cmd.schema_out and not cmd.schema_out.url.startswith("actors."):
                    setattr(self.schemas, process_url(cmd.schema_out.url), cmd.schema_out)

    @property
    def actors(self):
        if self._actors is None:
            self.reload()
        return self._actors

    @property
    def _client(self):
        if self._client_ is None:
            identity = j.tools.threebot.me.get(self.threebot_local_profile, needexist=False)
            nacl = identity.nacl

            server_pk = binascii.unhexlify(self.server_pk_hex)
            self._client_ = Client(kp=nacl.signing_key, server_pk=server_pk, host=self.host, port=self.port)

            authenticated = self._client_.execute_command("auth", identity.tid, nacl.verify_key_hex)
            if not authenticated:
                raise j.exceptions.Permission(f"authentication with gedis server {self.host}:{self.port} refused")

        return self._client_


    @property
    def _threebot_me(self):
        if not self._threebot_me_:
            self._threebot_me_ = j.tools.threebot.me.get(self.threebot_local_profile, needexist=False)
        return self._threebot_me_


class Client(object):
    """
    Implementation of the gedis client
    it uses SHS for handshake and implement RESP protocol on top
    """

    def __init__(self, kp, server_pk, host="127.0.0.1", port=8901):
        """        
        :param kp: key pair of the client
        :type kp: nacl.singing.SingingKey
        :param server_pk: serer public key hex encoded
        :type server_pk: string
        :param host: server address, defaults to "127.0.0.1"
        :type host: str, optional
        :param port: server port, defaults to 8901
        :type port: int, optional
        """
        self._protocol = ProtocolHandler()
        self._stream = SHSClient(host, port, kp, server_pub_key=server_pk)
        self._stream.open()

    def execute_command(self, *args):
        self._protocol.write_response(self._stream, args)
        resp = self._protocol.handle_request(self._stream)
        if isinstance(resp, Error):
            raise CommandError(resp.message)
        return resp
