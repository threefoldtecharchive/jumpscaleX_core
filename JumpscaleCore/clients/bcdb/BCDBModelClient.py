from Jumpscale import j


class BCDBModelClient(j.data.bcdb._BCDBModelBase):
    def _init(self, **kwargs):
        url = kwargs["url"]
        self.name = kwargs["name"]

        self.bcdb = j.data.bcdb.get(name=self.name)
        self.model = self.bcdb.model_get(url=url)
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
            assert self.model.schema.text
            self._rediscl_.execute_command(
                "bcdb_model_init", self.bcdb.name, self.model.schema.text, self.model.schema._md5
            )
            self.model.trigger_add(self._set_trigger)
            self._triggers = []
            self._kosmosinstance = None

    def get(self, id):
        if self.bcdb.readonly:
            key = f"{self.name}:data:{self.model.schema.url}"
            data = self._rediscl_.hget(key, str(id))
            ddata = j.data.serializers.json.loads(data)
            obj = self.model.new(ddata)
            obj, stop = self._triggers_call(obj=obj, action="get")
        else:
            obj = self.model.get(id)
        return obj

    def set(self, obj, triggers=True):
        if self.bcdb.readonly:
            if triggers:
                obj, stop = self._triggers_call(obj, action="set_pre")
                if stop:
                    assert obj.id
                    return obj
            key = f"{self.name}:data:{self.schema.url}"
            if obj.id:
                self._rediscl_.hset(key, str(obj.id), obj._json)
            else:
                r = self._rediscl_.execute_command("hsetnew", key, "0", obj._json)
                obj.id = int(r)
            if triggers:
                obj, stop = self._triggers_call(obj=obj, action="set_post")
            return obj
        else:
            return self.model.set(obj=obj)

    def delete(self, obj):
        if self.bcdb.readonly:
            obj, stop = self._triggers_call(obj=obj, action="delete")
            if stop:
                return obj
            key = f"{self.name}:data:{self.schema.url}"
            assert obj.id
            return self._rediscl_.hdel(key, str(obj.id))
        else:
            return self.model.delete(obj=obj)

    def reset(self):
        if self.bcdb.readonly:
            key = f"{self.name}:data:{self.schema.url}"
            self._rediscl_.hdel(key, "*")
        else:
            self.model.destroy()

    def _set_trigger(self, obj, action="set_pre", propertyname=None, **kwargs):
        if action == "set_pre":
            self.set(obj, triggers=False)
            # call through redis client the local BCDB
            # get data as json (from _data) and use redis client to set to server
            return obj, True
        return obj, False
