import imp
import os
import nacl

from Jumpscale import j
from redis.connection import ConnectionError

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
    port = 8900 (ipport)
    namespace = "default" (S)
    password_ = "" (S)
    ssl = False (B)
    ssl_keyfile = "" (S)
    ssl_certfile = "" (S)
    ssl_ca_certs = "" (S)
    """

    def _init(self, **kwargs):
        # j.clients.gedis.latest = self
        self._namespace = self.namespace
        self._actorsmeta = {}
        self.schemas = None
        self._actors = None
        self._code_generated_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "gedis", self.name, "client")
        j.sal.fs.createDir(self._code_generated_dir)
        j.sal.fs.touch(j.sal.fs.joinPaths(self._code_generated_dir, "__init__.py"))
        self._redis_ = None
        self._reset()

    def _update_trigger(self, key, val):
        self._reset()

    def _reset(self):
        self._redis_ = None  # connection to server
        # self._models = None
        self._actors = None

    def ping(self):
        test = self._redis.execute_command("ping")
        if test:
            return True
        return False

    def auth(self, bot_id):
        nacl_cl = j.data.nacl.get()
        nacl_cl._load_privatekey()
        signing_key = nacl.signing.SigningKey(nacl_cl.privkey.encode())
        epoch = str(j.data.time.epoch)
        signed_message = signing_key.sign(epoch.encode())
        cmd = "auth {} {} {}".format(bot_id, epoch, signed_message)
        res = self._redis.execute_command(cmd)
        return res

    def reload(self):
        self._log_info("reload")
        assert self.ping()
        self._actorsmeta = {}
        self._actors = GedisClientActors()
        self.schemas = GedisClientSchemas()

        # this will make sure we know the core schema's as used on server
        r = self._redis.execute_command("jsx_schemas_get")
        r2 = j.data.serializers.msgpack.loads(r)
        for key, data in r2.items():
            schema_text, schema_url = data
            if not j.data.schema.exists(md5=key):
                j.data.schema.get_from_text(schema_text, url=schema_url)
        cmds_meta = self._redis.execute_command("api_meta_get", self.namespace)
        cmds_meta = j.data.serializers.msgpack.loads(cmds_meta)
        if cmds_meta["cmds"] == {}:
            raise j.exceptions.Base("did not find any actors in namespace:%s" % self.namespace)
        for key, data in cmds_meta["cmds"].items():
            if "__model_" in key:
                raise j.exceptions.Base("aa")
            actor_name = key.split("__")[1]
            self._actorsmeta[actor_name] = j.servers.gedis._cmds_get(key, data)

        # at this point the schema's are loaded only for the namespace identified (is all part of metadata)
        for actorname, actormeta in self._actorsmeta.items():
            tpath = "%s/templates/GedisClientGenerated.py" % (j.clients.gedis._dirpath)
            actorname_ = actormeta.namespace + "_" + actorname
            dest = "/sandbox/var/codegen/gedis/%s/client/%s.py" % (self.name, actorname_)
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
            try:
                self.reload()
            except AttributeError as e:
                raise j.exceptions.Input(e)

        return self._actors

    @property
    def _redis(self):
        """
        this gets you a redis instance, when executing commands you have to send the name of the function without
        the postfix _cmd as is, do not capitalize it
        if it is testtest_cmd, then you should call it by testtest

        :return: redis instance
        """
        if self._redis_ is None:
            assert self.host != "0.0.0.0"
            addr = self.host
            port = self.port
            secret = self.password_

            self._log_info("redisclient: %s:%s " % (addr, port))

            self._redis_ = j.clients.redis.get(ipaddr=addr, port=port, password=secret, ping=True, fromcache=False)
        return self._redis_

    # def __getattr__(self, name):
    #     if name.startswith("_") or name in self._methods() or name in self._properties():
    #         return self.__getattribute__(name)
    #     return self.cmds.__getattribute__(name)

    def _methods(self, prefix=""):
        if prefix.startswith("_"):
            return JSConfigBase._methods(self, prefix=prefix)
        res = self.actors._methods()
        for i in ["ping"]:
            if i not in res:
                res.append(i)

        return res
