from Jumpscale import j


class BCDBModelClient(j.baseclasses.object):
    def _init(self, **kwargs):
        self.name = kwargs["name"]
        self.bcdb = j.data.bcdb.get(name=self.name)
        self.model = self.bcdb.model_get(url=kwargs["url"])
        self.schema = self.model.schema
        self.count = self.model.count

        if self.bcdb.readonly:
            self._rediscl_ = j.clients.bcdbmodel._rediscl_

        self.iterate = self.model.iterate
        self.search = self.model.search
        self.find = self.model.find
        self.new = self.model.new
        self.exists = self.model.exists
        self.find_ids = self.model.find_ids
        self.get_by_name = self.model.get_by_name

        if not self.bcdb.readonly:
            self.trigger_add = self.model.trigger_add
        else:
            self._rediscl_.execute_command(
                "bcdb_model_init", self.bcdb.name, self.model.schema.url, self.model.schema._md5, self.model.schema.text
            )

        self.index = self.model.index

        if self.bcdb.readonly:
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
            self._rediscl_.hdel(key, '*')
        else:
            return j.data.bcdb.instances.get(self.name).destroy()

    def _set_trigger(self, obj, action="set_pre", propertyname=None, **kwargs):
        if action == "set_pre":
            self.set(obj)
            # call through redis client the local BCDB
            # get data as json (from _data) and use redis client to set to server
            return obj, True
        return obj, False


class BCDBModelClientFactory(j.baseclasses.object):

    __jslocation__ = "j.clients.bcdbmodel"

    def _init(self, **kwargs):
        self._clients = j.baseclasses.dict()
        self._rediscl__ = None

    @property
    def _rediscl_(self):
        if not self._rediscl__:
            self._rediscl__ = j.clients.redis.get(port=6380)
        return self._rediscl__

    def server_config_reload(self):
        r = self._rediscl_.execute_command("bcdb_model_init", "", "", "", "")

    def get(self, url=None, schema=None, name=None):
        """
        :param name
        :return:
        """
        if schema:
            assert not url
            if isinstance(schema, str):
                schema = j.data.schema.get_from_text(schema)

            url = schema.url
        if not name:
            name = "system"
        if not url and not schema:
            url = "jumpscale.bcdb.user.2"
        key = f"{name}_{url}"
        if key not in self._clients:
            if name != "system" and not j.data.bcdb.exists(name):
                raise j.exceptions.Input("bcdb:'%s' has not been configured yet" % name)
            self._clients[key] = BCDBModelClient(name=name, url=url)
        return self._clients[key]

    @property
    def schemas(self):
        res = {}
        for name, bcdb in j.data.bcdb.instances.items():
            models = res.get(name, [])
            for model in bcdb.models:
                models.append(model)
            res[name] = models
        return res

    def test(self):
        """
        kosmos -p 'j.clients.bcdbmodel.test()'
        :return:
        """

        # j.servers.threebot.local_start_default(background=True)

        b = j.clients.bcdbmodel.get(url="jumpscale.sshclient.1")

        print(b.find())

        obj = b.find()[0]

        obj = b.get(id=obj.id)
        obj.addr = "localhost:%s" % j.data.idgenerator.generateRandomInt(1, 100000)
        obj.save()

        obj2 = b.get(id=obj.id)

        assert obj2.addr == obj.addr

        print("TEST OK")
