from Jumpscale import j


class BCDBModelClient(j.baseclasses.object):
    def _init(self, **kwargs):
        self.name = kwargs["name"]
        self.bcdb = j.data.bcdb.get(name=self.name)
        self.model = self.bcdb.model_get(url=kwargs["url"])
        self.schema = self.model.schema
        self.count = self.model.count
        self.index = self.model.index

        self.iterate = self.model.iterate
        self.search = self.model.search
        self.find = self.model.find
        self.new = self.model.new
        self.exists = self.model.exists
        self.find_ids = self.model.find_ids
        self.get_by_name = self.model.get_by_name

        if j.data.bcdb._master:
            self.trigger_add = self.model.trigger_add
        else:
            # means self.bcdb.readonly is True
            self._rediscl_ = j.clients.bcdbmodel._rediscl_
            self._rediscl_.execute_command(
                "bcdb_model_init", self.bcdb.name, self.model.schema.url, self.model.schema._md5, self.model.schema.text
            )
            self.model.trigger_add(self._set_trigger)

    def get(self, id):
        if self.bcdb.readonly:
            key = f"{self.name}:data:{self.model.schema.url}"
            data = self._rediscl_.hget(key, str(id))
            ddata = j.data.serializers.json.loads(data)
            return self.model.new(ddata)
        else:
            return self.model.get(id)

    def set(self, obj):
        if self.bcdb.readonly:
            key = f"{self.name}:data:{obj._schema.url}"
            if obj.id:
                self._rediscl_.hset(key, str(obj.id), obj._json)
            else:
                r = self._rediscl_.execute_command("hsetnew", key, "0", obj._json)
                obj.id = int(r)
                return obj
        else:
            return self.model.set(obj=obj)

    def delete(self, obj):
        if self.bcdb.readonly:
            key = f"{self.name}:data:{obj._schema.url}"
            assert obj.id
            return self._rediscl_.hdel(key, str(obj.id))
        else:
            return self.model.delete(obj=obj)

    def destroy(self):
        if self.bcdb.readonly:
            key = f"{self.name}:data:"
            self._rediscl_.hdel(key, "*")
        else:
            return j.data.bcdb.instances.get(self.name).destroy()

    def _set_trigger(self, obj, action="set_pre", propertyname=None, **kwargs):
        if action == "set_pre":
            self.set(obj)
            # call through redis client the local BCDB
            # get data as json (from _data) and use redis client to set to server
            return obj, True
        return obj, False
