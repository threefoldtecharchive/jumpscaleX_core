# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


# from importlib import import_module

import gevent
import time
from Jumpscale.clients.stor_zdb.ZDBClientBase import ZDBClientBase
from Jumpscale.clients.stor_rdb.RDBClient import RDBClient
from Jumpscale.clients.stor_sqlite.DBSQLite import DBSQLite
from .BCDBModel import BCDBModel
from .BCDBMeta import BCDBMeta

# from .BCDBDecorator import *
from .connectors.redis.RedisServer import RedisServer
from Jumpscale import j
import sys

JSBASE = j.baseclasses.object


class BCDB(j.baseclasses.object):
    def _init(self, name=None, storclient=None, reset=False):
        """
        :param name: name for the BCDB
        :param storclient: if storclient == None then will use sqlite db
        """

        self._redis_index = j.clients.redis.core
        if name is None:
            raise j.exceptions.Base("name needs to be specified")

        self.children = j.baseclasses.dict(name="BCDBMODELS")

        assert storclient
        if (
            not isinstance(storclient, ZDBClientBase)
            and not isinstance(storclient, RDBClient)
            and not isinstance(storclient, DBSQLite)
        ):
            raise j.exceptions.Base("storclient needs to be type: clients.zdb or clients.rdb or clients.sqlitedb")

        self.name = name
        self.dataprocessor_greenlet = None

        self._data_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb", self.name)
        self.storclient = storclient

        j.sal.fs.createDir(self._data_dir)

        self._sqlite_index_dbpath = "%s/sqlite_index.db" % self._data_dir

        self._init_props()

        if reset:
            self.meta = None
            self.reset()
            return
        else:
            self.meta = BCDBMeta(self)

        j.data.nacl.default

        self.dataprocessor_start()
        self._init_system_objects()

        # all the models are loaded at this point
        self.check()

        self._log_info("BCDB INIT DONE:%s" % self.name)

    def _init_props(self):

        self._sqlite_index_client = None

        self._schema_url_to_model = {}

        # needed for async processing
        self.results = {}
        self.results_id = 0

        self.acl = None
        self.user = None
        self.circle = None

    def _init_system_objects(self):

        assert self.name
        j.data.bcdb._children[self.name] = self

        if not j.data.types.string.check(self.name):
            raise j.exceptions.Base("name needs to be string")

        # need to do this to make sure we load the classes from scratch
        for item in ["ACL", "USER", "GROUP"]:
            key = "Jumpscale.data.bcdb.models_system.%s" % item
            if key in sys.modules:
                sys.modules.pop(key)

        from .models_system.ACL import ACL
        from .models_system.USER import USER
        from .models_system.CIRCLE import CIRCLE
        from .models_system.NAMESPACE import NAMESPACE

        self.acl = self.model_add(ACL(bcdb=self))
        self.user = self.model_add(USER(bcdb=self))
        self.circle = self.model_add(CIRCLE(bcdb=self))
        self.NAMESPACE = self.model_add(NAMESPACE(bcdb=self))

    def check(self):
        """
        at this point we have for sure the metadata loaded now we should see if the last record found can be found in the index
        :return:
        """

        def index_ok():
            for m in self.models:
                if m.schema.hasdata:
                    # we need to check that the id iterator has at least 1 item, its not a perfect check but better than nothing
                    if not m.index._ids_exists():
                        # means there is a real issue with an iterator
                        return False
            return True

        if not index_ok():
            # the index rebuild needs to completely remove the index, show a warning sign
            self._log_warning("we need to rebuild the full index because iterator was not complete")
            # there is no other way we can do this because without iterator the rebuild index cannot be done
            self.index_rebuild()

    def export(self, path=None, encrypt=True):
        if not path:
            raise j.exceptions.Base("export no path")
        for o in self.meta.schema_dicts:
            m = self.model_get(schema=o["text"])
            # to make schema export ID deterministic we add the mid at the beginning of the file name
            dpath = "%s/%s__%s__%s" % (path, m.mid, m.schema.url, m.schema._md5)
            j.sal.fs.createDir(dpath)
            dpath_file = "%s/meta.schema" % (dpath)
            j.sal.fs.writeFile(dpath_file, m.schema.text)
            for obj in list(m.iterate()):
                if obj._model.schema.url == o["url"]:
                    json = obj._json
                    if encrypt:
                        ext = ".encr"
                        json = j.data.nacl.default.encryptSymmetric(json)
                    else:
                        ext = ""
                    if "name" in obj._ddict:
                        dpath_file = "%s/%s__%s.json%s" % (dpath, obj.name, obj.id, ext)
                    else:
                        dpath_file = "%s/%s.json%s" % (dpath, obj.id, ext)
                    j.sal.fs.writeFile(dpath_file, json)

    def import_(self, path=None, reset=True):
        if not path:
            raise j.exceptions.Base("export no path")
        if reset:
            self.reset()
            if self.storclient:
                assert self.storclient.list() == [0]
        self._log_info("Load bcdb:%s from %s" % (self.name, path))
        assert j.sal.fs.exists(path)

        data = {}
        models = {}
        max = 0
        # first load all schemas
        for schema_id in j.sal.fs.listDirsInDir(path, False, dirNameOnly=True):
            mid, url, md5 = schema_id.split("__")
            schema_path = "%s/%s" % (path, schema_id)
            schema_text = j.sal.fs.readFile("%s/meta.schema" % schema_path)
            schema = j.data.schema.get_from_text(schema_text, multiple=False)
            model = self.model_get(schema=schema)
            models[md5] = model
        # now load the data
        for schema_id in j.sal.fs.listDirsInDir(path, False, dirNameOnly=True):
            schema_path = "%s/%s" % (path, schema_id)
            mid, url, md5 = schema_id.split("__")
            # print("MD5: %s" % md5)
            model = models[md5]
            assert model.schema._md5 == md5
            for item in j.sal.fs.listFilesInDir(schema_path, False):
                if j.sal.fs.getFileExtension(item) == "encr":
                    self._log("encr:%s" % item)
                    encr = True
                elif j.sal.fs.getFileExtension(item) == "json":
                    self._log("json:%s" % item)
                    encr = False
                else:
                    self._log("skip:%s" % item)
                    continue
                base = j.sal.fs.getBaseName(item)
                if base.find("__") != -1:
                    obj_id = int(base.split("__")[1].split(".")[0])
                else:
                    obj_id = int(base.split(".")[0])
                if obj_id in data:
                    raise j.exceptions.Base("id's need to be unique, cannot import")
                json = j.sal.fs.readFile(item, binary=encr)
                if encr:
                    json = j.data.nacl.default.decryptSymmetric(json)
                data[obj_id] = (md5, json)
                if obj_id > max:
                    max = obj_id

        if self.storclient:
            assert self.storclient.nsinfo["entries"] == 1
            lastid = 1

        # have to import it in the exact same order
        for i in range(1, max + 1):
            self._log("import: %s" % json)
            if self.storclient:
                if self.storclient.get(key=i - 1) is None:
                    obj = model.new()
                    obj.id = None
                    obj.save()
            if i in data:
                md5, json = data[i]
                model = models[md5]
                if self.storclient:
                    if self.storclient.get(key=i) is None:
                        # does not exist yet
                        try:
                            obj = model.new(data=json)
                        except:
                            raise j.exceptions.Base("can't get a new model based on json data:%s" % json)
                        if self.storclient:
                            obj.id = None
                    else:
                        obj = model.get(obj.id)
                        # means it exists, need to update, need to check if data is different only save if y
                else:
                    obj = model.get(i, die=False)
                    if not obj:
                        obj = model.new(data=json)
                obj.save()
                assert obj.id == i

    @property
    def sqlite_index_client(self):
        if self._sqlite_index_client is None:
            self._sqlite_index_client = j.clients.peewee.SqliteDatabase(self._sqlite_index_dbpath)
        return self._sqlite_index_client

    def sqlite_index_client_stop(self):
        if self._sqlite_index_client is not None:
            # todo: check that its open
            if not self._sqlite_index_client.is_closed():
                self._sqlite_index_client.close()
            self._sqlite_index_client = None

    def redis_server_start(self, port=6380, secret="123456"):
        self.redis_server_get(port=port, secret=secret)
        self.redis_server.start()

    def redis_server_wait_up(self, port, timeout=60):
        start = time.time()
        client = j.clients.redis.get(port=port)
        while start + timeout > time.time():
            try:
                client.ping()
                break
            except:
                pass
            gevent.sleep(0.5)
        else:
            raise j.exceptions.RuntimeError("Failed to wait for redisserver")

    def redis_server_get(self, port=6380, secret="123456"):
        self.redis_server = RedisServer(bcdb=self, port=port, secret=secret, addr="0.0.0.0")
        self.redis_server._init2(bcdb=self, port=port, secret=secret, addr="0.0.0.0")
        return self.redis_server

    def _data_process(self):
        # needs gevent loop to process incoming data
        # self._log_info("DATAPROCESSOR STARTS")
        while True:
            method, args, kwargs, event, returnid = self.queue.get()
            if args == ["STOP"]:
                break
            else:
                res = method(*args, **kwargs)
                if returnid:
                    self.results[returnid] = res
                event.set()
            self._data_process_1time()
        self.dataprocessor_greenlet = None
        if event:
            event.set()
        # self._log_warning("DATAPROCESSOR STOPS")

    def _data_process_1time(self, timeout=0, die=False):
        return

    def dataprocessor_start(self):
        """
        will start a gevent loop and process the data in a greenlet

        this allows us to make sure there will be no race conditions when gevent used or when subprocess
        main issue is the way how we populate the sqlite db (if there is any)

        :return:
        """
        if self.dataprocessor_greenlet is None:
            self.queue = gevent.queue.Queue()
            self.dataprocessor_greenlet = gevent.spawn(self._data_process)
            self.dataprocessor_state = "RUNNING"

    def dataprocessor_stop(self, force=False):

        if self.dataprocessor_greenlet:
            if self.dataprocessor_greenlet.started and not force:
                # stop dataprocessor
                self.queue.put((None, ["STOP"], {}, None, None))
                while self.queue.qsize() > 0:
                    # self._log_debug("wait dataprocessor to stop")
                    gevent.sleep(1)

        self._log_warning("DATAPROCESSOR & SQLITE STOPPED OK")
        # TODO: JO is this ok that it happens 2x
        return True

    def reset(self):
        """
        remove all data but the bcdb instance remains
        :return:
        """

        self.stop()  # will stop sqlite client and the dataprocessor

        assert self.storclient

        if self.storclient.type != "SDB":
            self.storclient.flush()  # not needed for sqlite because closed and dir will be deleted

        self._redis_reset()

        j.sal.fs.remove(self._data_dir)
        j.sal.fs.createDir(self._data_dir)
        # all data is now removed, can be done because sqlite client should be None

        # since delete the data directory above, we have to re-init the storclient
        # so it can do its things and re-connect properly
        self.storclient._init(nsname=self.storclient.nsname)

        self._init_props()
        if not self.meta:
            self.meta = BCDBMeta(self)

        self.meta.reset()  # will make sure the record 0 is written with empty metadata
        self._init_system_objects()

    def destroy(self):
        """
        removed all data and the bcbd instance
        :return:
        """

        self.reset()
        if self.name in j.data.bcdb._config:
            j.data.bcdb._config.pop(self.name)
        if self.name in j.data.bcdb._children:
            j.data.bcdb._children.pop(self.name)
        j.data.bcdb._config_write()
        for key in j.core.db.keys("bcdb:%s:*" % self.name):
            j.core.db.delete(key)

    def _redis_reset(self):
        # shouldnt this be part of the indexing class?
        # better not because then we rely on the indexer to be there and in reset function we don't init it
        for key in self._redis_index.keys("bcdb:%s*" % self.name):
            self._redis_index.delete(key)

    def stop(self):
        self._log_info("STOP BCDB")
        self.dataprocessor_stop(force=True)
        self.sqlite_index_client_stop()

        if self.storclient.type == "SDB":
            cl = self.storclient.sqlitedb
            if not cl.is_closed():
                cl.close()
            self.storclient.sqlitedb = None

    def index_rebuild(self):
        self._log_warning("REBUILD INDEX FOR ALL OBJECTS")
        # IF WE DO A FULL BLOWN REBUILD THEN WE NEED TO ITERATE OVER ALL OBJECTS AND CANNOT START FROM THE ITERATOR PER MODEL
        # this always needs to work, independent of state of index
        for model in self.models:
            # make sure indexes are empty
            model.index.destroy()
        first = True

        for id, data in self.storclient.iterate():
            if first:
                first = False
                continue
            jsxobj = self._unserialize(id, data)
            model = self.model_get(schema=jsxobj._schema)
            model.set(jsxobj, store=False, index=True)

    @property
    def models(self):
        # this needs to happen to make sure all models are loaded because there is lazy loading now
        for s in self.meta.schema_dicts:
            if s["url"] not in self._schema_url_to_model:
                assert s["url"]
                schema = j.data.schema.get_from_url(s["url"])
                self.model_get(schema=schema)
        for key, model in self._schema_url_to_model.items():
            yield model

    def model_get(self, schema=None, md5=None, url=None, reset=False):
        """
        will return the latest model found based on url, md5 or schema
        :param url:
        :return:
        """
        schema = self.schema_get(schema=schema, md5=md5, url=url)
        if schema.url in self._schema_url_to_model:
            model = self._schema_url_to_model[schema.url]
            model.schema_change(schema)
            self.meta._schema_set(schema)
            return model

        # model not known yet need to create
        self._log_info("load model:%s" % schema.url)

        model = BCDBModel(bcdb=self, schema_url=schema.url, reset=reset)

        self.model_add(model)

        return model

    def schema_get(self, schema=None, md5=None, url=None):
        """

        once a bcdb is known we should ONLY get a schema from the bcdb


        :param md5:
        :param url:
        :param die:
        :return:
        """

        if schema:
            assert md5 == None
            assert url == None
            if j.data.types.string.check(schema):
                schema_text = schema
                j.data.schema.models_in_use = False
                schema = j.data.schema.get_from_text(schema_text)
                j.data.schema.models_in_use = True
                self._log_debug("model get from schema:%s, original was text." % schema.url)
            else:
                self._log_debug("model get from schema:%s" % schema.url)
                if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
                    raise j.exceptions.Base("schema needs to be of type: j.data.schema.SCHEMA_CLASS")
        else:
            if url:
                assert md5 == None
                if not j.data.schema.exists(url=url):
                    # means we don't know it and it is not in BCDB either because the load has already happened
                    raise j.exceptions.Input("we could not find model from:%s, was not in bcdb or j.data.schema" % url)
                schema = j.data.schema.get_from_url(url)
            elif md5:
                assert url == None
                if not j.data.schema.exists(md5=md5):
                    raise j.exceptions.Input("we could not find model from:%s, was not in bcdb meta" % md5)
                schema = j.data.schema.get_from_md5(md5=md5)
            else:
                raise j.exceptions.Input("need to specify md5 or url")

        mid = self.meta._schema_set(schema)

        assert isinstance(schema, j.data.schema.SCHEMA_CLASS)

        return schema

    def model_add(self, model):
        """

        :param model: is the model object  : inherits of self.MODEL_CLASS
        :return: the model added or found in cache
        """
        if not isinstance(model, j.data.bcdb._BCDBModelClass):
            raise j.exceptions.Base("model needs to be of type:%s" % self._BCDBModelClass)

        if model.schema.url not in self._schema_url_to_model:
            self.meta._schema_set(model.schema)
            self._schema_property_add_if_needed(model.schema)
            self._schema_url_to_model[model.schema.url] = model

            self.children._add(model.schema.url, model)

        return self._schema_url_to_model[model.schema.url]

    def _schema_property_add_if_needed(self, schema, done=[]):
        """
        recursive walks over schema properties (multiple levels)
        if a sub property is a complex type by itself, then we need to make sure we remember the schema's also in BCDB
        :param schema:
        :return:
        """

        for prop in schema.properties:
            if prop.jumpscaletype.NAME == "list" and isinstance(prop.jumpscaletype.SUBTYPE, j.data.types._jsxobject):
                # now we know that there is a subtype, we need to store it in the bcdb as well
                s = prop.jumpscaletype.SUBTYPE._schema
                self.meta._schema_set(s)
                # now see if more subtypes
                if s._md5 not in done:
                    done.append(s._md5)
                    done = self._schema_property_add_if_needed(s)
            elif prop.jumpscaletype.NAME == "jsxobject":
                s = prop.jumpscaletype._schema
                self.meta._schema_set(s)
                # now see if more subtypes
                if s._md5 not in done:
                    done.append(s._md5)
                    done = self._schema_property_add_if_needed(s)

        return done

    def model_get_from_file(self, path):
        """
        add model to BCDB
        is path to python file which represents the model

        """
        self._log_debug("model get from file:%s" % path)
        obj_key = j.sal.fs.getBaseName(path)[:-3]
        cl = j.tools.codeloader.load(obj_key=obj_key, path=path, reload=False)
        model = cl(self)
        self.model_add(model)
        return model

    def models_add_threebot(self):
        self.models_add(self._dirpath + "/models_threebot")

    def models_add(self, path):
        """
        will walk over directory and each class needs to be a model
        when overwrite used it will overwrite the generated models (careful)

        support for *.py and *.toml files

        :param path:
        :return: None
        """
        self._log_debug("models_add:%s" % path)

        if not j.sal.fs.isDir(path):
            raise j.exceptions.Base("path: %s needs to be dir, to load models from" % path)

        pyfiles_base = []
        for fpath in j.sal.fs.listFilesInDir(path, recursive=True, filter="*.py", followSymlinks=True):
            pyfile_base = j.tools.codeloader._basename(fpath)
            if pyfile_base.find("_index") == -1:
                pyfiles_base.append(pyfile_base)

        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.toml", followSymlinks=True)
        # Try to load all schemas from directory
        # if one schema depends to another it will fail to load if the other one is not loaded yet
        # that's why we keep the errored schemas and put it to the end of the queue so it waits until every thing is
        # loaded and try again we will do that for 3 times as max for each schema
        errored = {}
        while tocheck != []:
            schemapath = tocheck.pop()
            bname = j.sal.fs.getBaseName(schemapath)[:-5]
            if bname.startswith("_"):
                continue
            dest = "%s/%s.py" % (path, bname)
            schema_text = j.sal.fs.readFile(schemapath)
            try:
                model = self.model_get(schema=schema_text)
            except Exception as e:
                if schemapath not in errored:
                    errored[schemapath] = 0
                errored[schemapath] += 1
                if errored[schemapath] > 4:
                    raise e
                tocheck.insert(0, schemapath)
                continue

            schema = model.schema
            toml_path = "%s.toml" % (schema.key)
            if j.sal.fs.getBaseName(schemapath) != toml_path:
                toml_path = "%s/%s.toml" % (j.sal.fs.getDirName(schemapath), schema.key)
                j.sal.fs.renameFile(schemapath, toml_path)
                schemapath = toml_path

        for pyfile_base in pyfiles_base:
            if pyfile_base.startswith("_"):
                continue
            path2 = "%s/%s.py" % (path, pyfile_base)
            self.model_get_from_file(path2)

    def _unserialize(self, id, data, return_as_capnp=False):
        """
        unserialzes data coming from database
        :param id:
        :param data:
        :param return_as_capnp:
        :param model:
        :return:
        """
        res = j.data.serializers.msgpack.loads(data)

        if len(res) == 3:
            nid, acl_id, bdata_encrypted = res
        else:
            raise j.exceptions.Base("not supported format")

        bdata = j.data.nacl.default.decryptSymmetric(bdata_encrypted)

        if return_as_capnp:
            return bdata
        else:
            obj = j.data.serializers.jsxdata.loads(bdata, bcdb=self)
            obj.nid = nid
            if not obj.id and id:
                obj.id = id
            if acl_id:
                obj.acl_id = acl_id
            return obj

    def obj_get(self, id):
        data = self.storclient.get(id)
        if data is None:
            return None
        return self._unserialize(id, data)

    def iterate(self, key_start=None, reverse=False, keyonly=False):
        """
        walk over all the namespace and yield each object in the database

        :param key_start: if specified start to walk from that key instead of the first one, defaults to None
        :param key_start: str, optional
        :param reverse: decide how to walk the namespace
                if False, walk from older to newer keys
                if True walk from newer to older keys
                defaults to False
        :param reverse: bool, optional
        :param keyonly: [description], defaults to False
        :param keyonly: bool, optional
        :raises e: [description]
        """
        if self.storclient:
            db = self.storclient
            for key, data in db.iterate(key_start=key_start, reverse=reverse, keyonly=keyonly):
                if key == 0:  # skip first metadata entry
                    continue
                if keyonly:
                    yield key
                elif data:
                    obj = self._unserialize(key, data)
                else:
                    obj = ""

                yield obj
        else:
            for key, data in self.sqlclient.iterate():
                if key == 0:  # skip first metadata entry
                    continue
                obj = self._unserialize(key, data)
                yield obj

    def get_all(self):
        return [obj for obj in self.iterate()]

    def __str__(self):
        out = "bcdb:%s\n" % self.name
        return out

    __repr__ = __str__
