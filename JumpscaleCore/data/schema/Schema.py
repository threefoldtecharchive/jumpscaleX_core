import os
from copy import copy
from .SchemaProperty import SchemaProperty
from Jumpscale import j


class Schema(j.baseclasses.object):
    def _init(self, text=None, url=None, md5=None):
        self._systemprops = {}
        self._obj_class = None
        self._capnp = None
        self._index_list = None

        self.systemprops = j.baseclasses.dict()

        self.text = text

        self.url = url

        assert md5
        self._md5 = md5

        self._schema_from_text(text)
        self.props = self._children

        if not self.url:
            raise j.exceptions.Input("url needs to be specified", data=text)

        self.key = j.core.text.strip_to_ascii_dense(self.url).replace(".", "_")

    @property
    def properties(self):
        return list(self._children.values())

    @property
    def url_str(self):
        u = self.url + ""
        # self._log_debug(u)
        if "schema" in u:
            u = u.split("schema", 1)[1]
        if "jumpscale" in u:
            u = u.split("jumpscale", 1)[1]
        return u

    # @property
    # def _path(self):
    #     return j.sal.fs.getDirName(os.path.abspath(__file__))

    def _error_raise(self, msg, e=None, schema=None):
        if self.url == "" and "url" in self._systemprops:
            self.url = self._systemprops["url"]
        out = "\nerror in schema:\n"
        out += "    url:%s\n" % self.url
        out += "    msg:%s\n" % j.core.text.prefix("    ", msg)
        if schema:
            out += "    schema:\n%s" % schema
        if e is not None:
            out += "\nERROR:\n"
            out += j.core.text.prefix("        ", str(e))
        raise j.exceptions.Base(out)

    def _proptype_get(self, txt):
        """
        if default value specified in the schema, will check how to convert it to a type
        :param txt:
        :return:
        """

        if "\\n" in txt:
            return j.data.types.get("multiline", default=txt)

        if "'" in txt or '"' in txt or txt.strip("'") == "":
            txt = txt.strip().strip('"').strip("'").strip()
            return j.data.types.get("string", default=txt)

        if "." in txt:
            return j.data.types.get("float", default=txt)

        if "true" in txt.lower() or "false" in txt.lower():
            return j.data.types.get("bool", default=txt)

        if "[]" in txt:
            return j.data.types.get("ls", default=txt)

        if j.data.types.int.checkString(txt):  # means is digit
            return j.data.types.get("i", default=txt)
        else:
            raise j.exceptions.Base("cannot find type for:%s" % txt)

    def _schema_from_text(self, text):
        """
        get schema object from schema text
        """

        self._log_debug("load schema", data=text)

        if text.count("@url") > 1:
            raise j.exceptions.Input("there should only be 1 url in the schema", data=text)
        if text.count("@url") == 0 and not self.url:
            raise j.exceptions.Input("url not specified", data=text)

        text = j.core.text.strip(text)

        systemprops = {}

        for line in text.split("\n"):
            line = line.strip()
            self._log_debug("L:%s" % line)
            if line.strip() == "":
                continue
            if line.startswith("@"):
                if "#" in line:
                    line, _ = line.split("#", 1)
                systemprop_name = line.split("=")[0].strip()[1:]
                systemprop_val = line.split("=")[1].strip()
                systemprops[systemprop_name] = systemprop_val.strip('"').strip("'")
                if systemprop_name == "url":
                    self.url = j.data.schema._urlclean(systemprops[systemprop_name])
                continue
            if line.startswith("#"):
                continue
            if "=" not in line:
                raise j.exceptions.Input(
                    "did not find =, need to be there to define field, line=%s\ntext:%s" % (line, text)
                )

            p = self._property_get_from_line(line)

        for key, val in systemprops.items():
            if not key == "url":
                self.systemprops[key] = val

    @property
    def _meta_url(self):
        assert self.url
        return j.data.schema.meta._data_url_get(self.url)

    def _property_get_from_line(self, line):
        assert self.url

        def _getdefault(txt):
            if '"' in txt or "'" in txt:
                txt = txt.strip().strip('"').strip("'").strip()
            if txt.strip() == "":
                return None
            txt = txt.strip()
            return txt

        assert ":" in line
        nr, line = line.split(":", 1)
        nr = int(nr)

        assert "=" in line
        key, _line = line.split("=", 1)
        key = key.replace("*", "").replace("&", "").lower().strip()

        line_original = copy(line)
        propname, line = line.split("=", 1)
        propname = propname.strip()

        line = line.strip()

        if "!" in line:
            line, pointer_type = line.split("!", 1)
            pointer_type = pointer_type.strip()
            pointer_type = j.data.schema._urlclean(pointer_type)
            line = line.strip()
        else:
            pointer_type = None

        if "#" in line:
            line, comment = line.split("#", 1)
            line = line.strip()
            comment = comment.strip()
        else:
            comment = ""

        p = SchemaProperty(nr=nr)

        name = propname + ""  # make sure there is copy
        if name.endswith("***"):
            name = name[:-3]
            p.index_text = True
        if name.endswith("**"):
            name = name[:-2]
            p.index = True
        if name.endswith("*"):
            raise j.exceptions.Input("key based indexing (*) for now not supported use **", data=line)
            # name = name[:-1]
            # p.index_key = True
        if name.startswith("&"):
            name = name[1:]
            p.unique = True
            # everything which is unique also needs to be indexed
            p.index_key = True

        if name in ["id"]:
            self._error_raise("do not use 'id' in your schema, is reserved for system.", data=text)
        elif name in ["name"]:
            p.unique = True
            # everything which is unique also needs to be indexed
            p.index_key = True

        if "(" in line:
            line_proptype = line.split("(")[1].split(")")[0].strip().lower()  # in between the ()
            self._log_debug("line:%s; lineproptype:'%s'" % (line_original, line_proptype))
            line_wo_proptype = line.split("(")[0].strip()  # before the (

            if pointer_type:
                pointer_type = j.data.schema._urlclean(pointer_type)
                default = pointer_type
                # means the default is a link to another object
            else:
                # will make sure we convert the default to the right possible type int,float, string
                default = _getdefault(line_wo_proptype)

            jumpscaletype = j.data.types.get(line_proptype, default=default)

            defvalue = None

        else:
            jumpscaletype = self._proptype_get(line)
            defvalue = None

        jumpscaletype._jsx_location

        p.name = name
        if defvalue:
            p._default = defvalue
        p.comment = comment
        p.jumpscaletype = jumpscaletype
        p.nr = nr

        self._children[p.name] = p
        # self.__dict__["property_%s" % p.name] = p

        assert p.jumpscaletype.NAME is not "list"

        return p

    @property
    def _capnp_id(self):
        if self._md5 == "":
            raise j.exceptions.Base("hash cannot be empty")
        return "f" + self._md5[1:16]  # first bit needs to be 1

    @property
    def _capnp_schema(self):
        if not self._capnp:
            self._capnp = j.data.capnp.getSchemaFromText(self._capnp_schema_text)
        return self._capnp

    @property
    def _capnp_schema_text(self):
        tpath = "%s/templates/schema.capnp" % self._dirpath
        # j.shell()
        _capnp_schema_text = j.tools.jinja2.template_render(path=tpath, reload=False, obj=self, objForHash=self._md5)
        if "@0x" not in _capnp_schema_text:
            j.shell()
        return _capnp_schema_text

    @property
    def objclass(self):
        if self._obj_class is None:

            if self._md5 in [None, ""]:
                raise j.exceptions.Base("md5 cannot be None")

            tpath = "%s/templates/JSXObject2.py" % self._dirpath

            # lets do some tests to see if it will render well, jinja doesn't show errors propertly
            for prop in self.properties:
                self._log_debug("prop for obj gen: %s:%s" % (prop, prop.js_typelocation))
                prop.capnp_schema
                prop.default_as_python_code
                prop.js_typelocation

            self._obj_class = j.tools.jinja2.code_python_render(
                name="schema_%s" % self.key, obj_key="JSXObject2", path=tpath, obj=self, objForHash=self._md5
            )

        return self._obj_class

    def index_needed(self):
        """
        :return:  (index_key, index_sql, index_text)
        each of them is True when there is an index like this on the schema
        otherwise False

        tells if we have to index that type

        """
        index_key = False
        index_sql = False
        index_text = False
        for p in self.properties:
            if p.index_text:
                index_text = True
            if p.index:
                index_sql = True
            index_key = False
            # if p.index_key:
            #     index_key = True
        return (index_key, index_sql, index_text)

    def new(self, capnpdata=None, serializeddata=None, datadict=None, model=None):
        """
        new schema_object using data and capnpbin

        :param serializeddata is data as serialized by j.serializers.jsxdata (has prio)
        :param capnpdata is data in capnpdata
        :param datadict is dict of arguments

        :param model: will make sure we save in the model
        :return:
        """

        # self._log_debug("LOADS:%s:%s" % (versionnr, obj_id))

        if serializeddata:
            assert isinstance(serializeddata, bytes)
            # schema does not have to be passed because the serialized data should have right md5 inside
            obj = j.data.serializers.jsxdata.loads(serializeddata, model=model)
        else:

            if capnpdata and isinstance(capnpdata, bytes):
                obj = self.objclass(schema=self, capnpdata=capnpdata, model=model, autosave=False)
            elif datadict and datadict != {}:
                obj = self.objclass(schema=self, datadict=datadict, model=model, autosave=False)
            elif capnpdata is None and serializeddata is None and datadict is None:
                obj = self.objclass(schema=self, model=model, autosave=False)
            else:
                raise j.exceptions.Base("wrong arguments to new on schema")

            obj._autosave_ = None  # so we fall back on defaults of the model.autosave

            if model:
                model._triggers_call(obj=obj, action="new")

        return obj

    # @property
    # def propertynames_index_sql(self):
    #     """
    #     list of the property names which are used for indexing in sql db (sqlite)
    #     :return:
    #     """
    #     res=[]
    #     for prop in self.properties:
    #         if prop.index:
    #             res.append(prop.name)
    #     return res

    @property
    def properties_index_sql(self):
        """
        list of the properties which are used for indexing in sql db (sqlite)
        :return:
        """
        res = []
        for prop in self.properties:
            if prop.index:
                res.append(prop)
            elif prop.is_jsxobject:
                for subprop in prop.jumpscaletype._schema.properties_index_sql:
                    sprop = SchemaProperty(
                        name=f"{prop.name}__{subprop.name}",
                        attr=f"{prop.name}.{subprop.name}",
                        jumpscaletype=subprop.jumpscaletype,
                        comment=subprop.comment,
                        nr=subprop.nr,
                        index=subprop.index,
                        unique=subprop.unique,
                    )
                    res.append(sprop)
        return res

    # @property
    # def properties_index_keys(self):
    #     """
    #     list of the properties which are used for indexing with keys
    #     :return:
    #     """
    #     res = []
    #     for prop in self.properties:
    #         if prop.index_key:
    #             res.append(prop)
    #     return res

    @property
    def properties_index_text(self):
        """
        list of the properties which are used for indexing with keys
        :return:
        """
        res = []
        for prop in self.properties:
            if prop.index_text:
                res.append(prop)
        return res

    @property
    def properties_unique(self):
        """
        list of the properties which are used for indexing with keys
        :return:
        """
        res = []
        for prop in self.properties:
            if prop.unique:
                res.append(prop)
        return res

    @property
    def propertynames(self):
        """
        lists all the property names
        :return:
        """
        return list(self._children.keys())

    @property
    def _json(self):
        out = "{"
        out += '"url":"%s",' % self.url
        for item in self.propertynames:
            prop = self.props[item]
            out += '"%s":"%s",' % (str(prop.name), str(prop.jumpscaletype.NAME))
        out = out.rstrip(",")
        out += "}"
        return out

    def __str__(self):
        out = "## SCHEMA: %s\n\n" % self.url
        for item in self.properties:

            out += str(item) + "\n"
        out += str(self.systemprops)
        return out

    def __eq__(self, other):
        if other is None:
            return False
        return other._md5 == self._md5

    __repr__ = __str__
