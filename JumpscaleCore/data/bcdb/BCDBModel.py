from Jumpscale import j


from .BCDBDecorator import queue_method, queue_method_results

JSBASE = j.baseclasses.object
INT_BIN_EMPTY = b"\xff\xff\xff\xff"  # is the empty value for in our key containers

# from .BCDBModelIndex import BCDBModelIndex
from .BCDBIndexMeta import BCDBIndexMeta
from .BCDBModelBase import BCDBModelBase


class BCDBModel(BCDBModelBase):
    def __init__(self, bcdb, schema_url=None, reset=False):
        """

        delivers interface how to deal with data in 1 schema

        for query example see http://docs.peewee-orm.com/en/latest/peewee/query_examples.html

        e.g.
        ```
        query = self.index.name.select().where(index.cost > 0)
        for item in self.select(query):
            print(item.name)
        ```
        """

        JSBASE.__init__(self)

        # we should have a schema
        if schema_url:
            self.schema = j.data.schema.get_from_url(schema_url)
        else:
            if hasattr(self, "_SCHEMA"):  # what is that _schema ?
                self.schema = j.data.schema.get_from_text(self._SCHEMA, newest=True)
            else:
                self.schema = self._schema_get()  # _schema_get is overrided by classes like ACL USER CIRCLE NAMESPACE
                if not self.schema:
                    j.exceptions.JSBUG("BCDB Model needs a schema object or text")

        self.bcdb = bcdb
        self._md5_previous_ = None

        self.readonly = False
        self._index_ = None  # if set it will make sure data is automatically set from object
        self.nosave = False

        self.instances = []

        if self.storclient and self.storclient.type == "ZDB":
            # is unique id for a bcdbmodel (unique per storclient !)
            self.key = "%s_%s" % (self.storclient.nsname, self.schema.url)
        else:
            self.key = self.schema.url
        self.key = self.schema.key

        self._data_dir = j.sal.fs.joinPaths(self.bcdb._data_dir, self.key)
        j.sal.fs.createDir(self._data_dir)

        self._kosmosinstance = None

        self._sonic_client = None
        # self.cache_expiration = 3600

        self._triggers = []

        if reset:
            indexklass = self._index_class_generate()
            self._index_ = indexklass(model=self, reset=True)
            self.destroy()

        self.trigger_add(self._maintenance)

    def _maintenance(self, model=None, obj=None, action=None, kosmosinstance=None, propertyname=None):
        if action == "schema_change":
            for obj in self.instances:
                # make sure we attach the right model to the obj
                obj._model = self.bcdb.model_get(url=obj._schema.url)
        if action == "stop":
            for obj in self.instances:
                obj.stop()

    @property
    def index(self):
        if not self._index_:
            indexklass = self._index_class_generate()
            self._index_ = indexklass(model=self, reset=False)
        return self._index_

    def _index_class_generate(self):
        """

        :param schema: is schema object j.data.schema... or text
        :return: class of the model which is used for indexing

        """
        self._log_debug("generate schema index:%s" % self.schema.url)

        # model with info to generate
        imodel = BCDBIndexMeta(schema=self.schema)
        imodel.include_schema = True
        tpath = "%s/templates/BCDBModelIndexClass.py" % j.data.bcdb._dirpath
        name = "bcdbindex_%s_%s" % (self.schema.url, self.schema._md5)
        name = name.replace(".", "_")
        # if self.schema.url == "jumpscale.example.car.1":
        #     j.shell()
        #     w
        myclass = j.tools.jinja2.code_python_render(
            name=name,
            path=tpath,
            objForHash=self.schema._md5,
            reload=True,
            schema=self.schema,
            bcdb=self.bcdb,
            index=imodel,
            model=self,
        )

        return myclass

    def schema_change(self, schema, obj=None):
        assert isinstance(schema, j.data.schema.SCHEMA_CLASS)

        # make sure model has the latest schema
        if self.schema._md5 != schema._md5:
            self.schema = schema
            self._log_info("schema change")
            self._triggers_call(obj, "schema_change", None)

    def stop(self):
        self._triggers_call(obj=None, action="stop")

    @property
    def sonic_client(self):
        if not self._sonic_client:
            self._sonic_client = j.clients.sonic.get_client_bcdb()
        return self._sonic_client

    def _schema_get(self):
        return None

    @property
    def storclient(self):
        return self.bcdb.storclient

    def trigger_add(self, method):
        """
        see docs/baseclasses/data_mgmt_on_obj.md

        triggers are called with obj,action,propertyname as kwargs

        return obj or None

        :param method:
        :return:
        """
        if method not in self._triggers:
            self._triggers.append(method)

    def _triggers_call(self, obj, action=None, propertyname=None):
        """
        will go over all triggers and call them with arguments given
        see docs/baseclasses/data_mgmt_on_obj.md

        return obj, stop

        """
        model = self
        kosmosinstance = self._kosmosinstance
        stop = False
        for method in self._triggers:
            obj2 = method(model=model, obj=obj, kosmosinstance=kosmosinstance, action=action, propertyname=propertyname)
            if isinstance(obj2, list) or isinstance(obj2, tuple):
                obj2, stop = obj2
                if stop:
                    return obj, stop
            if isinstance(obj2, j.data.schema._JSXObjectClass):
                # only replace if right one returned, otherwise ignore
                obj = obj2
            else:
                if obj2 is not None:
                    raise j.exceptions.Base("obj return from action needs to be a JSXObject or None")
        return obj, stop

    # def cache_reset(self):
    #     self.obj_cache = {}

    @queue_method
    def index_ready(self):
        """
        doesn't do much, just makes sure that we wait that queue has been processed upto this point
        :return:
        """
        return True

    @queue_method
    def index_rebuild(self, nid=1):
        self.index.destroy(nid=nid)
        self._log_warning("will rebuild index for:%s" % self)
        for obj in self.iterate(nid=nid):
            self.set(obj, store=False, index=True)

    @queue_method
    def delete(self, obj, force=True):
        self.bcdb._is_writable_check()

        if isinstance(obj, int):
            assert obj > 0
            self.storclient.delete(obj)
            self.index.delete_by_id(obj_id=obj, nid=1)

        elif isinstance(obj, j.data.schema._JSXObjectClass):
            assert obj.nid
            if obj.id is not None:
                obj, stop = self._triggers_call(obj=obj, action="delete")
                # if obj.id in self.obj_cache:
                #     self.obj_cache.pop(obj.id)
                if not stop:
                    self.storclient.delete(obj.id)
                    self.index.delete_by_id(obj_id=obj.id, nid=obj.nid)
        else:
            raise j.exceptions.Input("obj need to be JSXObject or int")

    def check(self, obj):
        if not isinstance(obj, j.data.schema._JSXObjectClass):
            raise j.exceptions.Base("argument needs to be a jsx data obj")
        assert obj.nid

    @queue_method
    def set_dynamic(self, data, obj_id=None, nid=1):
        """
        if string -> will consider to be json
        if binary -> will consider data for capnp
        if obj -> will check of JSOBJ
        if ddict will put inside JSOBJ
        """
        self.bcdb._is_writable_check()
        if j.data.types.string.check(data):

            data = j.data.serializers.json.loads(data)
            if obj_id is None and "id" in data:
                obj_id = data["id"]
            if nid is None:
                if "nid" in data:
                    nid = data["nid"]
                else:
                    raise j.exceptions.Base("need to specify nid")
            obj = self.schema.new(datadict=data, model=self)
            obj.nid = nid
        elif j.data.types.bytes.check(data):
            obj = self.schema.new(serializeddata=data, model=self)
            if obj_id is None:
                raise j.exceptions.Base("objid cannot be None")
            if not obj.nid:
                if nid:
                    obj.nid = nid
                else:
                    raise j.exceptions.Base("need to specify nid")
        elif isinstance(data, j.data.schema._JSXObjectClass):
            obj = data
            if obj_id is None and obj.id is not None:
                obj_id = obj.id
            if not obj.nid:
                if nid:
                    obj.nid = nid
                else:
                    raise j.exceptions.Base("need to specify nid")
        elif j.data.types.dict.check(data):
            if obj_id is None and "id" in data:
                obj_id = data["id"]
            if "nid" not in data or not data["nid"]:
                if nid:
                    data["nid"] = nid
                else:
                    raise j.exceptions.Base("need to specify nid")
            obj = self.schema.new(datadict=data)
            obj.nid = nid
        else:
            raise j.exceptions.Base("Cannot find data type, str,bin,obj or ddict is only supported")
        if not obj.id:
            obj.id = obj_id  # do not forget
        return self.set(obj)

    def get_by_name(self, name, nid=1, die=True):
        args = {"name": name}
        list_obj = self.find(nid=nid, **args)
        if len(list_obj) > 0:
            return list_obj[0]
        if die:
            raise j.exceptions.NotFound("cannot find data with name : %s" % name)

    def search(self, text, property_name=None):
        # FIXME: get the real nids
        objs = self.sonic_client.query(self.bcdb.name, "1:{}".format(self.key), text)
        res = []
        for obj in objs:
            parts = obj.split(":")
            if (property_name and parts[1] == property_name) or (not property_name):
                res.append(self.get(int(parts[0])))
        return res

    def upgrade(self, obj):
        self.bcdb._is_writable_check()
        obj._model.schema_change(obj._model.bcdb.schema_get(url=obj._schema.url))
        j.shell()
        return obj

    @queue_method_results
    def set(self, obj, index=True, store=True):
        """
        :param obj
        :return: obj
        """
        self.check(obj)

        if store:
            obj, stop = self._triggers_call(obj, action="set_pre")
            if stop:
                assert obj.id
                return obj

            self.bcdb._is_writable_check()

            # later:
            if obj.acl_id is None:
                obj.acl_id = 0

            if obj._acl is not None:
                if obj.acl.id is None:
                    # need to save the acl
                    obj.acl.save()
                else:
                    acl2 = obj._model.bcdb.acl.get(obj.acl.id)
                    if acl2 is None:
                        # means is not in db
                        obj.acl.save()
                    else:
                        if obj.acl.md5 != acl2.md5:
                            obj.acl.id = None
                            obj.acl.save()  # means there is acl but not same as in DB, need to save
                            self._obj_cache_reset()
                obj.acl_id = obj.acl.id

            try:
                bdata = obj._data
            except Exception as e:
                if str(e).find("has no such member") != -1:
                    msg = str(e).split("no such member", 1)[1].split("stack:")
                    raise j.exceptions.Base("Could not serialize capnnp message:%s" % msg)
                else:
                    raise e

            bdata_encrypted = j.data.nacl.default.encryptSymmetric(bdata)
            assert obj.nid > 0
            l = [obj.nid, obj.acl_id, bdata_encrypted]
            data = j.data.serializers.msgpack.dumps(l)

            # PUT DATA IN DB
            if obj.id is None:
                # means a new one
                obj.id = self.storclient.set(data)
                if obj.id == 0:
                    # need to skip the first one
                    obj.id = self.storclient.set(data)

                new = True
                # self._log_debug("NEW:\n%s" % obj)
            else:
                new = False
                try:
                    self.storclient.set(data, key=obj.id)
                except Exception as e:
                    if str(e).find("only update authorized") != -1:
                        raise j.exceptions.Base("cannot update object:%s\n with id:%s, does not exist" % (obj, obj.id))
                    raise

        if index:
            # self._log_debug(obj)
            # print(obj)
            if not store:  # need to make sure index is clean, used during rebuild index (is safer)
                self.index.delete(obj)
            try:
                self.index.set(obj)
            except j.clients.peewee.IntegrityError as e:
                # this deals with checking on e.g. uniqueness
                # j.shell()
                raise j.exceptions.Input("Could not insert object, unique constraint failed:%s" % e, data=obj)

                obj.id = None
                if str(e).find("UNIQUE") != -1:
                    raise j.exceptions.Input("Could not insert object, unique constraint failed:%s" % e, data=obj)
                raise

        obj, stop = self._triggers_call(obj=obj, action="set_post")

        # if self.storclient.type == "RDB":
        #     # TODO: should be part of the storclient itself and we should use lua code on the redis, is much faster
        #     self.storclient._redis
        #     # idea is to allow subscribers to listen to changes, each change needs to get a unique nr
        #     # so remote users can replicate where needed, or can be used to do replication
        #     j.shell()
        #     self.storclient

        return obj

    def _dict_process_out(self, ddict):
        """
        whenever dict is needed this method will be called before returning
        :param ddict:
        :return:
        """
        return ddict

    def _dict_process_in(self, ddict):
        """
        when data is inserted back into object
        :param ddict:
        :return:
        """
        return ddict

    def new(self, data=None, nid=1, **kwargs):

        if kwargs != {}:
            data = kwargs
        if data and isinstance(data, dict):
            data = self._dict_process_in(data)
        elif isinstance(data, str) and j.data.types.json.check(data):
            data = j.data.serializers.json.loads(data)

        if data:
            if isinstance(data, dict):
                obj = self.schema.new(datadict=data, model=self)
            elif isinstance(data, bytes):
                try:

                    data = j.data.serializers.json.loads(data)
                    obj = self.schema.new(datadict=data, model=self)
                except:
                    obj = self.schema.new(serializeddata=data, model=self)

            elif isinstance(data, j.data.schema._JSXObjectClass):
                obj = self.schema.new(datadict=data._ddict, model=self)
            else:
                raise j.exceptions.Base("need dict")
        else:
            obj = self.schema.new()
            obj._model = self

        obj = self._methods_add(obj)
        obj.nid = nid
        obj, stop = self._triggers_call(obj=obj, action="new")

        return obj

    def _methods_add(self, obj):
        return obj

    def exists(self, obj_id):
        #
        return self.get(obj_id=obj_id, die=False) != None

    @queue_method_results
    def get(self, obj_id, return_as_capnp=False, die=True):
        """
        @PARAM id is an int or a key
        @PARAM capnp if true will return data as capnp binary object,
               no hook will be done !
        @RETURN obj    (.index is in obj)
        """
        if obj_id in [None, 0, "0", b"0"]:
            raise j.exceptions.Base("id cannot be None or 0")

        # if self.obj_cache is not None and usecache:
        #     # print("use cache")
        #     if obj_id in self.obj_cache:
        #         epoch, obj = self.obj_cache[obj_id]
        #         if j.data.time.epoch > self._cache_expiration + epoch:
        #             self.obj_cache.pop(obj_id)
        #             # print("dirty cache")
        #         else:
        #             # print("cache hit")
        #             return obj

        data = self.storclient.get(obj_id)

        if not data:
            if die:
                raise j.exceptions.NotFound(f"could not find obj with id:{obj_id} of {self.schema.url}")
            else:
                return None

        obj = self.bcdb._unserialize(obj_id, data, return_as_capnp=return_as_capnp, schema=self.schema)
        if obj._schema.url == self.schema.url and obj._schema._md5 == self.schema._md5:
            obj, stop = self._triggers_call(obj=obj, action="get")
        else:
            raise j.exceptions.JSBUG(
                "no object with id {} found in {}, this means the index gave back an id which is not part of this model, different schema url.".format(
                    obj_id, self
                )
            )

        # self.obj_cache[obj_id] = (j.data.time.epoch, obj)  #FOR NOW NO CACHE, UNSAFE
        return obj

    def destroy(self, nid=1):
        self._log_warning("destroy: %s nid:%s" % (self, nid))
        assert isinstance(nid, int)
        assert nid > 0
        for obj_id in self.find_ids(nid=nid):
            self.storclient.delete(obj_id)
        self.index.destroy()
        j.sal.fs.remove(self._data_dir)

    def _list_ids(self, nid=1):
        return self.find_ids(nid=nid)
        # res = []
        # for obj_id in self.index._id_iterator(nid=nid):
        #     res.append(obj_id)
        # return res

    @property
    def ids_names(self):
        """
        return list of [[name,id]]
        :return:
        """
        query = "SELECT id,name FROM %s; " % self.index.sql_table_name
        cursor = self.index.db.execute_sql(query)
        return [(item[0], item[1]) for item in cursor]

    @property
    def ids(self):
        """
        return list of ids (read from index)
        :return:
        """
        query = "SELECT id FROM %s; " % self.index.sql_table_name
        cursor = self.index.db.execute_sql(query)
        return [item[0] for item in cursor]

    def iterate(self, nid=1):
        """
        walk over objects which are of type of this model
        """
        # for obj_id in self.index._id_iterator(nid=nid):
        #     # self._log_debug("iterate:%s" % obj_id)
        #     assert obj_id > 0
        #     o = self.get(obj_id, die=False)
        #     if not o:
        #         continue
        #     yield o
        for id in self.find_ids(nid=nid):
            o = self.get(id)
            yield o

    def _text_index_content_pre_(self, property_name, val, obj_id, nid=1):
        """ A hook to be called before setting to the full text index
        """
        return property_name, val, obj_id, nid

    def _find_query(self, nid, _count=False, offset=None, limit=None, **kwargs):
        values = []
        field = "id"
        if _count:
            field = 'count("id")'
        whereclause = ""
        if kwargs:
            for key, val in kwargs.items():
                if whereclause:
                    whereclause += " AND"
                if isinstance(val, bool):
                    if val:
                        val = 1
                    else:
                        val = 0
                whereclause += f" {key} = ?"
                values.append(val)

        return self.query_model([field], whereclause, limit=limit, offset=offset, values=values)

    def query_model(self, fields, whereclause=None, limit=None, offset=None, values=None):
        fieldstring = ", ".join(fields)
        query = f"select {fieldstring} FROM {self.index.sql_table_name} "
        if whereclause:
            query += f"where {whereclause}"
        if limit and isinstance(limit, int):
            query += f" LIMIT {limit}"
        if offset and isinstance(offset, int):
            query += f" OFFSET {offset}"
        query += ";"
        return self.index.db.execute_sql(query, values)

    def find_ids(self, nid=None, limit=None, offset=None, **kwargs):
        """
        is an iterator !!!
        :param nid:
        :param kwargs:
        :return:
        """
        if not nid:
            nid = 1
        cursor = self._find_query(nid, limit=limit, offset=offset, **kwargs)
        r = cursor.fetchone()
        res = []
        while r:
            # the id NEEDS to exist on the model  (THIS IS A SHORTCUT FIX, BUT FIRST WANT TO SEE IF I CAN FIX IT)
            # if self.exists(r[0]):
            res.append(r[0])
            r = cursor.fetchone()

        return res

    def query(self, query, values=None):
        """
        returns id's

        ps there are lots of good tools which allow you to build sql statements graphically
        e.g. razorsql

        to load the sqlite db go to : {DIR_BASE}/var/bcdb/myjobs/sqlite_index.db
        in this case name of this bcdb is myjobs

        :param sqlquery:
        :return: sqlite cursor
        """
        return self.index.db.execute_sql(query, values)

    def find(self, nid=None, limit=None, offset=None, **kwargs):
        res = []
        for id in self.find_ids(nid=nid, limit=limit, offset=offset, **kwargs):
            try:
                obj = self.get(id)
            except Exception as e:
                if isinstance(e, j.exceptions.NotFound):
                    self._log_warning(
                        "I found object with id:%s in index but not in backendstor, will ignore in find" % id
                    )
                    obj = None
                    continue
                else:
                    raise
            if obj:
                res.append(obj)
        return res

    def count(self, nid=None, **kwargs):
        res = self._find_query(nid, True, **kwargs).fetchone()
        return res[0]

    def __str__(self):
        out = "model:%s\n" % self.schema.url
        # out += j.core.text.prefix("    ", self.schema.text)
        return out

    __repr__ = __str__

    # def find(self, nid=1, **args):
    #     """
    #     is a the retrieval part of a very fast indexing system
    #     e.g.
    #     self.get_from_keys(name="myname",nid=2)
    #     :return:
    #     """
    #     delete_if_not_found = True
    #     # if no args are provided that mean we will do a get all
    #     if len(args.keys()) == 0:
    #         res = []
    #         for obj in self.iterate(nid=nid):
    #             if obj is None:
    #                 raise j.exceptions.Base("iterate should not return None, ever")
    #             res.append(obj)
    #         return res
    #
    #     ids = self.index._key_index_find(nid=nid, **args)
    #
    #     def check2(obj, args):
    #         dd = obj._ddict
    #         for propname, val in args.items():
    #             if not propname in dd:
    #                 self._log_warning("need to update an object, could not find propname:%s" % propname, data=dd)
    #                 return propname
    #             if dd[propname] != val:
    #                 return False
    #         return True
    #
    #     res = []
    #     for id_ in ids:
    #         # ids right now come from redis, they should be fone when model is gone, when they exist there they should really exist
    #         res2 = self.get(id_, die=True)
    #         if res2 is None:
    #             # only when we use file based id index then there can be situation where id is in file but not in db
    #             # if id index in redis which is default now then there needs to be consistency between id index & db
    #             if len(args) == 0:
    #                 # means we were iterating so there could be
    #                 if delete_if_not_found:
    #                     for key, val in args.items():
    #                         self._key_index_delete(key, val, id_, nid=nid)
    #         else:
    #             # we now need to check if there was no false positive
    #             check = check2(res2, args)
    #             if isinstance(check, str):
    #                 # FOR NOW NO UPGRADE POSSIBLE, JUST FAIL
    #                 # j.shell()
    #                 # from pudb import set_trace
    #                 #
    #                 # set_trace()
    #                 # res2 = self.upgrade(res2)
    #                 # check = check2(res2, args)
    #                 if isinstance(check, str):
    #                     # means we still don't find the argument, the upgrade did notwork
    #                     raise j.exceptions.JSBUG(
    #                         "find was done on argument:%s which does not exist in model." % res, data=obj
    #                     )
    #             elif check:
    #                 res.append(res2)
    #             else:
    #                 self._log_warning("index system produced false positive, is not abnormal")
    #
    #     return res
