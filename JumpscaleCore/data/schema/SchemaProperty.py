from Jumpscale import j

JSBASE = j.baseclasses.object


class SchemaProperty(j.baseclasses.object):
    def _init(self, **kwargs):

        # following 2 need to be given
        self.nr = kwargs["nr"]

        self.name = kwargs.get("name", "")
        self.attr = kwargs.get("attr", "")
        self.jumpscaletype = kwargs.get("jumpscaletype", None)
        self.comment = kwargs.get("comments", "")
        self._default = None
        self.index = kwargs.get("index", False)  # as used in sqlite
        # self.index_key = False  # is for indexing the keys
        self.index_text = False  # is for full text index
        self.unique = False  # to check if type is unique or not
        if self.name in ["schema"]:
            raise j.exceptions.Base("cannot have property name:%s" % self.name)

    # @property
    # def _hash(self):
    #     o = ""
    #     for x in self.__dict__.values():
    #         o += str(x)
    #     return j.data.hash.md5_string(o)
    #
    # def __eq__(self, other):
    #     assert isinstance(other, SchemaProperty)
    #     return other._hash == self._hash

    @property
    def capnp_schema(self):
        return self.jumpscaletype.capnp_schema_get(self.name_camel, self.nr)

    @property
    def default(self):
        if self._default:
            return self._default
        return self.jumpscaletype.default_get()

    @property
    def has_jsxobject(self):
        return self.is_list_jsxobject or self.is_jsxobject

    @property
    def is_list_jsxobject(self):
        if self.jumpscaletype.BASETYPE == "list":
            if self.jumpscaletype.SUBTYPE.BASETYPE == "JSXOBJ":
                return True
        return False

    @property
    def is_jsxobject(self):
        if self.jumpscaletype.BASETYPE == "JSXOBJ":
            return True
        return False

    @property
    def is_list(self):
        if self.jumpscaletype.NAME == "list":
            return True
        return False

    @property
    def is_primitive(self):
        if self.is_serialized:
            return False
        if self.is_complex_type:
            return False
        if self.jumpscaletype.BASETYPE in ["string", "int", "dict", "bytes", "bool", "float"]:
            return True
        return False

    @property
    def is_serialized(self):
        return isinstance(self.jumpscaletype, j.data.types._TypeBaseClassSerialized)

    @property
    def is_complex_type(self):
        return isinstance(self.jumpscaletype, j.data.types._TypeBaseObjFactory)

    @property
    def is_primitive_serialized(self):
        if self.jumpscaletype.NAME in ["json", "yaml", "dict"]:
            return True
        return False

    @property
    def default_as_python_code(self):
        if self.is_primitive:
            return self.jumpscaletype.python_code_get(self.default)
        return None

    @property
    def name_camel(self):
        out = ""
        for item in self.name.split("_"):
            if out is "":
                out = item.lower()
            else:
                out += item.capitalize()
        return out

    @property
    def name_str(self):
        return "%-20s" % self.name

    @property
    def js_typelocation(self):
        return self.jumpscaletype._jsx_location

    def __str__(self):
        if not self.jumpscaletype.NAME == "list":
            out = "prop:%-25s %s" % (self.name, self.jumpscaletype.NAME)
        else:
            out = "prop:%-25s %s" % (self.name, self.jumpscaletype)

        # if self.pointer_type:
        #     out += " !%s" % self.pointer_type
        return out

    __repr__ = __str__
