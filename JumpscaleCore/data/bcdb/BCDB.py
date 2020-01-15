# from importlib import import_module

import gevent
import time
import atexit
from Jumpscale.clients.stor_zdb.ZDBClientBase import ZDBClientBase
from Jumpscale.clients.stor_rdb.RDBClient import RDBClient
from Jumpscale.clients.stor_sqlite.DBSQLite import DBSQLite
from .BCDBModel import BCDBModel

from Jumpscale import j
import sys


class BCDB(j.baseclasses.object):
    def _init(self, name=None, storclient=None, reset=False, readonly=False):
        """
        :param name: name for the BCDB
        :param storclient: if storclient is None then will use sqlite db
        """
        if name is None:
            raise j.exceptions.Base("name needs to be specified")

        assert storclient

        if not storclient.get(0):
            r = storclient.set(b"INIT")
            # this is to not have id 0, otherwise certain tests which check on value in 0 get confused
            assert storclient.get(0)

        if (
            not isinstance(storclient, ZDBClientBase)
            and not isinstance(storclient, RDBClient)
            and not isinstance(storclient, DBSQLite)
        ):
            raise j.exceptions.Base("storclient needs to be type: clients.zdb or clients.rdb or clients.sqlitedb")

        self.name = name

        self._init_props_()

        # self._redis_index = j.clients.redis.core
        self._data_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb", self.name)

        # self._lock_file = "%s/lock" % self._data_dir
        # self.lock = j.tools.filelock.lock_get(self._lock_file)

        self._urls_load()  # make sure we know which url's linked to this bcdb

        self.storclient = storclient

        j.sal.fs.createDir(self._data_dir)
        self.readonly = readonly

        if self.readonly:
            self._log_info("sqlite file is in readonly mode for: '%s'" % self.name)
            self._sqlite_index_dbpath = "file:%s/sqlite_index.db?mode=ro" % self._data_dir
        else:
            self._sqlite_index_dbpath = "file:%s/sqlite_index.db" % self._data_dir

        if reset:
            self.reset()

        j.data.nacl.default
        self.dataprocessor_start()

        self.check()

        # dataprocessor_stop
        atexit.register(self.stop)
        self._log_info("BCDB INIT DONE:%s" % self.name)

    @property
    def models(self):
        for url in self._urls:
            if url not in self._models:
                self.model_get(url=url, die=False)
        return self._models

    def _is_writable_check(self):
        return not self.readonly

    def start(self):
        self._init_props_()
        self._init_system_objects()
        self.dataprocessor_start()

    def stop(self):
        """
        make sure the bcdb is initialized with default values & all is stopped
        """
        for model in self._models.values():
            # lets make sure the triggers are fired
            model.stop()

        self.dataprocessor_stop()
        self.sqlite_index_client_stop()
        if self.storclient.type == "SDB":
            cl = self.storclient.sqlitedb
            if cl and not cl.is_closed():
                cl.close()
            self.storclient.sqlitedb = None
        self._init_props_()
        # self._shutdown_ = True
        self._log_info(" * STOP BCDB: %s" % self.name)

    def _init_props_(self):

        self._sqlite_index_client = None

        self.dataprocessor_greenlet = None

        # self._shutdown_ = False  # if set it means we should not use bcdb any more

        # needed for async processing
        self.results = {}
        self.results_id = 0

        self.acl = None
        self.user = None
        self.circle = None

        self._models = j.baseclasses.dict(name="BCDBMODELS")  # is model based on url as key

    def _init_system_objects(self):

        assert self.name

        if not j.data.types.string.check(self.name):
            raise j.exceptions.Base("name needs to be string")

        # think no longer needed
        # for item in ["ACL", "USER", "GROUP"]:
        #     key = "Jumpscale.data.bcdb.models_system.%s" % item
        #     if key in sys.modules:
        #         sys.modules.pop(key)

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
        # need to implement something here

        if self.readonly:
            return

        # def index_ok():
        #     for m in self.models:
        #         # we need to check that the id iterator has at least 1 item, its not a perfect check but better than nothing
        #         if not m.index._ids_exists():
        #             # means there is a real issue with an iterator
        #             return False
        #     return True
        #
        # if not index_ok():
        #     # the index rebuild needs to completely remove the index, show a warning sign
        #     self._log_warning("we need to rebuild the full index because iterator was not complete")
        #     # there is no other way we can do this because without iterator the rebuild index cannot be done
        #     self.index_rebuild()

        return

    def export(self, path=None, encrypt=False, reset=True, data=True, yaml=True):
        """Export all models and objects

        :param path: path to export to
        :type path: str
        :param encrypt: encrypt data before exporting, defaults to True
        :type encrypt: bool, optional
        :param reset: reset the export path before exporting, defaults to True
        :type reset: bool, optional
        """

        j.data.bcdb.threebot_zdb_sonic_start()

        if not path:
            path = j.core.tools.text_replace("{DIR_VAR}/bcdb_exports/%s" % self.name)

        if reset:
            j.sal.fs.remove(path)
        j.sal.fs.createDir(path)

        # lets copy the config info from bcdb
        if self.name != "system":
            config = j.data.bcdb._config[self.name]
            j.data.serializers.yaml.dump(f"{path}/bcdbconfig.yaml", config)

        vs = list(self.models.values())
        for m in vs:
            print("export model: ", m)
            dpath = f"{path}/{m.schema.url}"
            print("  datapath: ", dpath)
            j.sal.fs.createDir(dpath)
            j.sal.fs.writeFile(f"{dpath}/_schema.toml", m.schema.text)
            url2 = m.schema.url.replace(".", "__")

            # lets keep history of the schema's in the export
            source_schema_hist_path = j.core.tools.text_replace("{DIR_CFG}/bcdb/%s.toml" % url2)
            j.sal.fs.copyFile(source_schema_hist_path, "%s/schema_hist.toml" % dpath)

            for obj in list(m.iterate()):
                # print("  writing object: ", obj)
                assert obj._model.schema.url == m.schema.url
                assert obj._model.schema._md5 == obj._schema._md5
                print(" - %s:%s" % (obj._schema.url, obj.id))
                if data:
                    data = obj._data
                    # print("OBJ._DATA:", data)
                    if encrypt:
                        data = j.data.nacl.default.encryptSymmetric(data)
                        j.sal.fs.writeFile("%s/%s.data.encr" % (dpath, obj.id), data)
                    else:
                        j.sal.fs.writeFile("%s/%s.data" % (dpath, obj.id), data)
                if yaml:
                    # try:
                    #     C = j.data.serializers.toml.dumps(obj._ddict)
                    #     ext = "toml"
                    # except:
                    C = j.data.serializers.yaml.dumps(obj._ddict)
                    ext = "yaml"
                    if hasattr(obj, "name") and "/" not in obj.name:
                        # print(" - %s:%s" % (obj._schema.url, obj.name))
                        dpath_file = "%s/%s.%s" % (dpath, obj.name, ext)
                    else:
                        # print(" - %s:%s" % (obj._schema.url, obj.id))
                        dpath_file = "%s/%s.%s" % (dpath, obj.id, ext)
                    if encrypt:
                        C = j.data.nacl.default.encryptSymmetric(C)
                        j.sal.fs.writeFile(dpath_file + ".encr", C)
                    else:
                        j.sal.fs.writeFile(dpath_file, C)

    def import_(self, path, interactive=True):
        """Import models and objects from path.

        :param path: path to import data from
        :type path: str
        :param interactive: interactively ask user, defaults to True
        :type interactive: bool, optional
        """
        if not j.sal.fs.exists(path):
            raise j.exceptions.Base("path does not exist")

        if interactive:
            if not j.core.tools.ask_yes_no("Importing will reset your BCDB. Are you sure you want to continue?"):
                return

        self.reset()

        self._log_info("Load bcdb:%s from %s" % (self.name, path))
        assert j.sal.fs.exists(path)

        data = {}
        models = {}
        schemas = {}
        paths = j.sal.fs.listDirsInDir(path, False, dirNameOnly=False)

        for url_path in paths:
            # load all schemas first to make sure all models schemas are loaded when refrenced by parent schemas
            print(f"processing schema {url_path}")
            schema_text = j.sal.fs.readFile("%s/_schema.toml" % url_path)
            url = j.sal.fs.getBaseName(url_path)
            schema = j.data.schema.get_from_text(schema_text, url=url)
            schemas[url] = schema

        for url_path in paths:
            print(f"processing {url_path}")
            url = j.sal.fs.getBaseName(url_path)
            model = self.model_get(schema=schemas[url])
            models[url] = model
            if model._index_:
                model._index_.destroy()
            for item in j.sal.fs.listFilesInDir(url_path, False):
                print(f"item {item}")
                if item.endswith("_schema.toml"):
                    continue
                if item.endswith("schema_hist.toml"):
                    continue
                print(f"processing item: {item}")
                ext = j.sal.fs.getFileExtension(item)
                if ext == "data" or ext == "datae":
                    self._log("encr:%s" % item)
                    data2 = j.sal.fs.readFile(item, binary=True)
                    if ext == "datae":
                        data2 = j.data.nacl.default.decryptSymmetric(data2)
                    obj = j.data.serializers.jsxdata.loads(data2)
                    # print(f"data decrypted {data}")
                    data[obj.id] = (url, obj._ddict)
                elif ext in ["toml", "yaml"] or ext in ["tomle", "yamle"]:
                    if ext == "toml":
                        self._log("toml:%s" % item)
                        datadict = j.data.serializers.toml.load(item)
                    elif ext == "yaml":
                        self._log("yaml:%s" % item)
                        datadict = j.data.serializers.yaml.load(item)
                    elif ext == "tomle":
                        self._log("toml:%s" % item)
                        data = j.sal.fs.readFile(item)
                        data = j.data.nacl.default.decryptSymmetric(data)
                        datadict = j.data.serializers.toml.loads(data)
                    elif ext == "yamle":
                        self._log("yaml:%s" % item)
                        data = j.sal.fs.readFile(item)
                        data = j.data.nacl.default.decryptSymmetric(data)
                        datadict = j.data.serializers.yaml.loads(data)

                    data[datadict["id"]] = (url, datadict)
                else:
                    self._log("skip:%s" % item)
                    continue

        max_id = max(list(data.keys()) or [0])

        next_id = 1
        if isinstance(self.storclient, ZDBClientBase):
            next_id = self.storclient.next_id

        to_remove = []

        # have to import it in the exact same order
        for i in range(1, max_id + 1):
            # print(f"i: {i}")
            if i not in data:
                if i < next_id:
                    continue
                print(f"{i} doesn't exist in data.. ")
                self.storclient.set("")
                to_remove.append(i)
            else:
                url, obj_data = data[i]
                model = models[url]

                print(f"setting obj {obj_data} using {model.schema.url}, id should be {i}")

                del obj_data["id"]
                obj = model.new(data=obj_data)
                obj.save()
                assert obj.id == i

        print("Cleaning up empty objects")
        for i in to_remove:
            self.storclient.delete(i)

    @property
    def sqlite_index_client(self):
        if self._sqlite_index_client is None:
            self._sqlite_index_client = j.clients.peewee.SqliteDatabase(
                self._sqlite_index_dbpath, uri=True, pragmas={"journal_mode": "wal"}
            )

        return self._sqlite_index_client

    def sqlite_index_client_stop(self):
        if self._sqlite_index_client is not None:
            # todo: check that its open
            if not self._sqlite_index_client.is_closed():
                self._sqlite_index_client.close()
            self._sqlite_index_client = None

    def redis_server_start(self, port=6380, secret="123456"):
        self.redis_server = j.data.bcdb.redis_server_get(port=port, secret=secret)
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
            self._log_info("** START DATA PROCESSOR FOR :%s" % self.name)
            self.queue = gevent.queue.Queue()
            self.dataprocessor_greenlet = gevent.spawn(self._data_process)
            self.dataprocessor_state = "RUNNING"

    def dataprocessor_stop(self, force=False):

        # print("** STOP DATA PROCESSOR FOR :%s" % self.name)

        if self.dataprocessor_greenlet:
            if self.dataprocessor_greenlet.started and not force:
                if self.queue.qsize() == 0:
                    return
                # stop dataprocessor
                self.queue.put((None, ["STOP"], {}, None, None))
                while self.queue.qsize() > 0:
                    # self._log_debug("wait dataprocessor to stop")
                    gevent.sleep(0.1)

        self.dataprocessor_greenlet = None

        self._log_warning("DATAPROCESSOR & SQLITE STOPPED OK")

        return True

    def index_reset(self):
        self.stop()  # will stop sqlite client and the dataprocessor
        assert self.storclient
        # self._redis_reset()
        if self.storclient.type != "SDB":
            j.sal.fs.remove(self._data_dir)
        else:
            # is sqlite db can only remove the index
            j.sal.fs.remove(f"{self._data_dir}/sqlite_index.db")
            j.sal.fs.remove(f"{self._data_dir}/sqlite_index.db-shm")
            j.sal.fs.remove(f"{self._data_dir}/sqlite_index.db-wal")
        j.sal.fs.createDir(self._data_dir)

    def reset(self):
        """
        remove all data but the bcdb instance remains
        :return:
        """
        self.stop()  # will stop sqlite client and the dataprocessor

        assert self.storclient

        if self.storclient.type == "SDB":
            self.storclient.close()
        else:
            self.storclient.flush()  # not needed for sqlite because closed and dir will be deleted

        # self._redis_reset()
        j.sal.fs.remove(self._data_dir)
        j.sal.fs.createDir(self._data_dir)
        # all data is now removed, can be done because sqlite client should be None

        # since delete the data directory above, we have to re-init the storclient
        # so it can do its things (e.g. create sqlitedb, init redis, ...) and re-connect properly
        self.storclient._connect()

        if not self.storclient.get(0):
            r = self.storclient.set(b"INIT")
            # this is to not have id 0, otherwise certain tests which check on value in 0 get confused
            assert self.storclient.get(0)

        self.start()

    def destroy(self):
        """
        removed all data and the bcdb instance
        :return:
        """

        self.reset()
        if self.name in j.data.bcdb._config:
            j.data.bcdb._config.pop(self.name)
        j.data.bcdb._config_write()
        for key in j.core.db.keys("bcdb:%s:*" % self.name):
            j.core.db.delete(key)

        if self.name in j.data.bcdb._children:
            j.data.bcdb.instances.pop(self.name)

    # def _redis_reset(self):
    #     # shouldnt this be part of the indexing class?
    #     # better not because then we rely on the indexer to be there and in reset function we don't init it
    #     for key in self._redis_index.keys("bcdb:%s*" % self.name):
    #         self._redis_index.delete(key)

    def _urls_load(self):
        """
        need to remeber which url's are linked to this bcdb
        :return:
        """
        path = j.core.tools.text_replace("{DIR_CFG}/bcdb/urls_%s.yaml" % self.name)
        if j.sal.fs.exists(path):
            data = j.sal.fs.readFile(path)
            self._urls = j.data.serializers.yaml.loads(data)
        else:
            self._urls = []

    def _url_set(self, url):
        if not self._urls:
            self._urls_load()
        if url not in self._urls:
            path = j.core.tools.text_replace("{DIR_CFG}/bcdb/urls_%s.yaml" % self.name)
            self._urls.append(url)
            j.data.serializers.yaml.dump(path, self._urls)

    def index_rebuild(self):
        """
        :return:
        """
        self._log_warning("REBUILD INDEX FOR ALL OBJECTS")
        # IF WE DO A FULL BLOWN REBUILD THEN WE NEED TO ITERATE OVER ALL OBJECTS AND CANNOT START FROM THE ITERATOR PER MODEL
        # this always needs to work, independent of state of index

        first = True
        self.index_reset()
        self.start()

        if not self._urls:
            # need to look for urls
            for id, data in self.storclient.iterate():
                md5 = self._unserialize_md5(data)
                if not j.data.schema.exists(md5=md5):
                    raise j.exceptions.Input(
                        f"could not find schema with md5:{md5}, make sure use option recover schema's"
                    )
                s = j.data.schema.get(md5=md5)
                self._url_set(s.url)

        for id, data in self.storclient.iterate():
            if first:
                first = False
                continue
            jsxobj = self._unserialize(id, data)
            model = self.model_get(schema=jsxobj._schema)
            model.set(jsxobj, store=False, index=True)

    def model_get(self, schema=None, md5=None, url=None, reset=False, triggers=True, die=True):
        """
        will return the latest model found based on url, md5 or schema
        :param url:
        :return:
        """

        if url and not die and not j.data.schema.meta._schema_exists(url):
            return

        schema = self.schema_get(schema=schema, md5=md5, url=url)

        if schema.url in self.models:
            if schema._md5 != self.models[schema.url].schema._md5:
                # this means we found model in mem but schema changed in mean time
                # need to use the new one now
                self._models[schema.url].schema = schema
                if triggers:
                    self._models[schema.url].schema_change(schema)
                    # don't add the obj, because need to do for all obj
            return self._models[schema.url]

        # model not known yet need to create
        self._log_info("load model:%s" % schema.url)

        self._url_set(schema.url)

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
            assert md5 is None
            assert url is None
            if j.data.types.string.check(schema):
                schema_text = schema
                # j.data.schema.models_in_use = False
                schema = j.data.schema.get_from_text(schema_text)
                # j.data.schema.models_in_use = True
                self._log_debug("model get from schema:%s, original was text." % schema.url)
            else:
                # self._log_debug("model get from schema:%s" % schema.url)
                if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
                    raise j.exceptions.Base("schema needs to be of type: j.data.schema.SCHEMA_CLASS")
        else:
            if url:
                url = j.data.schema._urlclean(url)
                assert md5 is None
                if not j.data.schema.exists(url=url):
                    # means we don't know it and it is not in BCDB either because the load has already happened
                    raise j.exceptions.Input("we could not find model from:%s, was not in bcdb or j.data.schema" % url)
                schema = j.data.schema.get_from_url(url)
            elif md5:
                assert url is None
                if not j.data.schema.exists(md5=md5):
                    raise j.exceptions.Input("we could not find model from:%s, was not in bcdb meta" % md5)
                schema_md5 = j.data.schema.get_from_md5(md5=md5)
                schema = j.data.schema.get_from_url(schema_md5.url)
            else:
                raise j.exceptions.Input("need to specify md5 or url")

        assert isinstance(schema, j.data.schema.SCHEMA_CLASS)
        return schema

    def model_add(self, model):
        """

        :param model: is the model object  : inherits of self.MODEL_CLASS
        :return: the model added or found in cache
        """

        if not isinstance(model, j.data.bcdb._BCDBModelClass):
            raise j.exceptions.Base("model needs to be of type:%s" % self._BCDBModelClass)

        if not j.data.schema.exists(md5=model.schema._md5):
            # means has not been set in model yet, lets find out why
            j.shell()

        self._schema_property_add_if_needed(model.schema)

        self._models[model.schema.url] = model

        self._url_set(model.schema.url)

        return self._models[model.schema.url]

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
                if not j.data.schema.exists(url=s.url):
                    # should be there lets see why not
                    j.shell()
                # now see if more subtypes
                if s._md5 not in done:
                    done.append(s._md5)
                    done = self._schema_property_add_if_needed(s)
            elif prop.jumpscaletype.NAME == "jsxobject":
                s = prop.jumpscaletype._schema
                if s.url not in j.data.schema.schemas_loaded:
                    # should be there lets see why not
                    j.shell()
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
        cl, changed = j.tools.codeloader.load(obj_key=obj_key, path=path, reload=False)
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
        :return: urls of the models
        """

        models_urls = []
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
                if model.schema.url not in models_urls:
                    models_urls.append(model.schema.url)
            except Exception as e:
                if schemapath not in errored:
                    errored[schemapath] = 0
                errored[schemapath] += 1
                if errored[schemapath] > 4:
                    raise e
                tocheck.insert(0, schemapath)
                continue

            schema = model.schema

        for pyfile_base in pyfiles_base:
            if pyfile_base.startswith("_"):
                continue
            path2 = "%s/%s.py" % (path, pyfile_base)
            model = self.model_get_from_file(path2)
            if model.schema.url not in models_urls:
                models_urls.append(model.schema.url)
        return models_urls

    def _unserialize_md5(self, data):
        res = j.data.serializers.msgpack.loads(data)

        if len(res) == 3:
            nid, acl_id, bdata_encrypted = res
        else:
            raise j.exceptions.Base("not supported format")

        data = j.data.nacl.default.decryptSymmetric(bdata_encrypted)

        versionnr = int.from_bytes(data[0:1], byteorder="little")

        if versionnr == 3:
            obj_id = int.from_bytes(data[1:5], byteorder="little")
            md5bin = data[5:21]
            md5 = md5bin.hex()
            return md5
        else:
            raise

    def _unserialize(self, id, data, return_as_capnp=False, schema=None):
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
            if not schema:
                md5bin = bdata[5:21]
                md5 = md5bin.hex()
                schema = j.data.schema.get_from_md5(md5)
            model = self.model_get(schema=schema)
            obj = j.data.serializers.jsxdata.loads(bdata, model=model)
            if schema:
                if not obj._schema == schema:
                    j.shell()
                assert obj._schema == schema
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

    def migrate_models(self, from_url, to_url):
        from_model = self.model_get(url=from_url)
        to_model = self.model_get(url=to_url)

        for obj in from_model.find():
            new_obj = to_model.new()
            for prop in to_model.schema.properties:
                if prop.name in from_model.schema.propertynames and getattr(obj, prop.name):
                    setattr(new_obj, prop.name, getattr(obj, prop.name))
                elif prop in to_model.schema.properties_index_sql and not getattr(new_obj, prop.name):
                    # this is an indexed field and doesn't have a default value so we have to generate some data in it
                    setattr(new_obj, prop.name, j.data.idgenerator.generateXCharID(20))
                    # TODO: thats an ugly hack not sure this is ok, maybe better to just fail

            new_obj.save()
            obj.delete()

    def __str__(self):
        out = "bcdb:%s\n" % self.name
        return out

    __repr__ = __str__
