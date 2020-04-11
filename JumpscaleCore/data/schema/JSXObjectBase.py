from Jumpscale import j


class JSXObjectBase(j.baseclasses.object):
    def _init_pre(self, capnpdata=None, datadict=None, schema=None):
        self._capnp_obj_ = None
        self._autosave = False
        # schema is the schema of the obj, can be subobj
        # the model needs to be empty if subobj
        assert schema
        self._schema = schema
        self._deserialized_items = {}
        self._changed_deserialized_items = False
        self._load_from_data(capnpdata=capnpdata)  # ONLY LOADS THE self._capnp_obj_
        # self._changed_props = []
        self.id = None
        self._ignore_model_autosave = False

        if datadict:
            self._data_update(datadict)

        # self._logger_enable()

    def _defaults_set(self):
        # j.debug()
        self._ignore_model_autosave = True
        for prop in self._schema.properties:
            # name = prop.name
            setattr(self, prop.name, prop.default)
        self._ignore_model_autosave = False

    @property
    def _readonly(self):
        if self._root._model:
            return self._root._model.readonly
        return False

    @property
    def _nosave(self):
        if self._root._model:
            return self._root._model.nosave
        return False

    @property
    def _capnp_schema(self):
        return self._schema._capnp_schema

    def _data_update(self, datadict):
        if datadict == None:
            datadict = {}
        if not isinstance(datadict, dict):
            raise j.exceptions.Base("need to be dict, was:\n%s" % datadict)
        if self._model is not None and self._parent is None:
            datadict = self._model._dict_process_in(datadict)
        for key, val in datadict.items():
            try:
                setattr(self, key, val)
            except Exception as e:
                if isinstance(e, ValueError):
                    msg = "cannot update data for: %s  set prop %s with '%s'" % (self._schema.url, key, val)
                    e.args = (msg,)
                raise e

    def _load_from_data(self, capnpdata=None):
        """
        THIS ERASES EXISTING DATA !!!

        :param data: can be binary (capnp), str=json, or dict
        :return:
        """
        if isinstance(capnpdata, bytes):
            self._capnp_obj_ = self._capnp_schema.from_bytes_packed(capnpdata, traversal_limit_in_words=1.8446744e19)
        elif capnpdata == None:
            self._capnp_obj_ = self._capnp_schema.new_message()
            self.acl_id = 0
            self._acl = None
            self._defaults_set()  # only do when new message
        else:
            raise RuntimeError()

    def _hr_get_properties(self, props):
        """human readable format for given properties

        :param props: properties as a dict
        :type props: dict
        :return: humand readable string
        :rtype: str
        """
        out = "\n"
        keys = [name for name in props.keys()]
        keys.sort()
        for key in keys:
            item = props[key]
            out += "- %-30s: %s\n" % (key, item)
        return out

    def _hr_get(self, exclude=[]):
        """
        human readable test format
        """
        return self._hr_get_properties(self._ddict_hr_get(exclude=exclude))

    def check_empty_indexed_fields(self):
        for prop in self._model.schema.properties_index_sql:
            if "." in prop.name:
                raise j.exceptions.Input("cannot be . in property")
            if "__" in prop.name:
                # handle indexed subobject field
                props = prop.name.split("__")
                value = eval(f"self.{props[0]}.{props[1]}")
            else:
                # handle indexed object field
                value = eval(f"self.{prop.name}")
            if not value and not isinstance(value, (int, float, complex)):
                raise j.exceptions.Input("an indexed (sql) field cannot be empty:%s" % prop.name, data=self)

        for prop in self._model.schema.properties_index_text:
            if eval(f"self.{prop.name}") is None:
                raise j.exceptions.Input("an indexed (text) field cannot be empty:%s" % prop.name, data=self)

    @property
    def _data(self):
        self._capnp_obj  # leave, is to make sure we have error if something happens
        return j.data.serializers.jsxdata.dumps(self)

    @property
    def _ddict_hr(self):
        """
        human readable dict
        """
        d = self._ddict_hr_get(ansi=False)
        return d

    @property
    def _ddict_json_hr(self):
        """
        json readable dict
        """
        return j.data.serializers.json.dumps(self._ddict_hr)

    @property
    def _json(self):
        return j.data.serializers.json.dumps(self._ddict)  # DO NOT USE THE HR ONE

    @property
    def _toml(self):
        return j.data.serializers.toml.dumps(self._ddict)

    @property
    def _msgpack(self):
        return j.data.serializers.msgpack.dumps(self._ddict)

    # def __setattr__(self, name, value):
    #     if name in self.__class__.__slots__:
    #         self.__dict__[name] = value
    #         return
    #     if name in self.__class__.__props__:
    #         self.__dict__[name] = value
    #         return
    #     raise j.exceptions.Base("protected property on jsxobj:%s" % name)

    def __eq__(self, val):
        if isinstance(val, str) or isinstance(val, int) or isinstance(val, float) or isinstance(val, set):
            return False
        if not isinstance(val, JSXObjectBase):
            tt = j.data.types.get("jsxobject", self._schema.url)
            if hasattr(self, "_parent"):
                val = tt.clean(val, parent=self._parent)
            else:
                val = tt.clean(val)
        if id(val) == id(self):
            return True
        return self._data == val._data

    def __hash__(self):
        return hash(j.data.hash.md5_string(self._data))

    def __repr__(self):
        # FIXME: breaks in some cases in docsites generation needs to be cleanly implemented
        return self._str_get(ansi=True)

    def __str__(self):
        out = self._str_get(ansi=False)
        return out
