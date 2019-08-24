from Jumpscale import j
from Jumpscale.data.types.TypeBaseClasses import TypeBaseObjFactory


class JSXObjectTypeFactory(TypeBaseObjFactory):
    """
    jumpscale data object as result of using j.data.schema.
    """

    BASETYPE = "JSXOBJ"
    NAME = "jsxobject,o"
    CUSTOM = True

    def __init__(self, default=None):
        self.BASETYPE = "JSXOBJ"
        self.SUBTYPE = None
        if not default:
            raise j.exceptions.Input("Cannot init JSDataObjectFactory without md5 or url")
        self._default = default
        self._schema_ = None

    @property
    def _schema(self):
        """
        JSX schema for the child
        :return:
        """
        if self._schema_ is None:
            if self._default.startswith("md5:"):
                self._schema_md5 = self._default[4:]  # md5 is directly given
            elif self._default.startswith("sid:"):
                raise j.exceptions.JSBUG("sid no longer used")
            else:
                s = j.data.schema.get_from_url(url=self._default)
            self._schema_md5 = s._md5

            self._schema_ = j.data.schema.get_from_md5(md5=self._schema_md5)
        return self._schema_

    def python_code_get(self, value):
        return None

    def fromString(self, val):
        """
        will use json
        """
        return self.clean(val)

    def toData(self, val, model=None):
        val2 = self.clean(val, model=model)
        return j.data.serializers.jsxdata.dumps(val2)

    def toString(self, val):
        """
        will use json
        :param v:
        :return:
        """
        val = self.clean(val)
        return val._json

    def check(self, value):
        return isinstance(value, j.data.schema._JSXObjectClass)

    def default_get(self, model=None):
        if model:
            bcdb = model._bcdb
        else:
            bcdb = None
        return self._schema.new(bcdb=bcdb)

    def clean(self, value, model=None):
        """

        :param value: is the object which needs to be converted to a data object
        :param model: when model specified (BCDB model) can be stored in BCDB
        :return:
        """
        if model:
            bcdb = model.bcdb
        else:
            bcdb = None
        if isinstance(value, j.data.schema._JSXObjectClass):
            return value
        elif not value:
            return self._schema.new(bcdb=bcdb)
        elif isinstance(value, bytes):
            obj = j.data.serializers.jsxdata.loads(value, bcdb=bcdb)
            # when bytes the version of the jsxobj & the schema is embedded in the bin data
            return obj
        elif isinstance(value, dict):
            return self._schema.new(datadict=value, bcdb=bcdb)
        elif isinstance(value, j.baseclasses.object_config):
            return value._data
        else:
            raise j.exceptions.Input("can only accept dataobj, bytes (capnp) or dict as input for jsxobj")

    def toHR(self, v):
        v = self.clean(v)
        return str(v)

    def capnp_schema_get(self, name, nr):
        return "%s @%s :Data;" % (name, nr)

    def toml_string_get(self, value, key):
        raise j.exceptions.Value("not implemented")


# class JSConfigObjectFactory(TypeBaseObjFactory):
#     '''
#     jumpscale object which inherits from j.baseclasses.object_config
#     '''
#     NAME =  'jsconfigobject,configobj'
#
#     def __init__(self,default=None):
#
#         self.BASETYPE = 'capnpbin'
#         self.SUBTYPE = None
#
#         self._default = default
#
#     def check(self, value):
#         return isinstance(value, j.baseclasses.object_config)
#
#     def clean(self,value):
#         if isinstance(value, j.baseclasses.object_config):
#             return value
#         raise NotImplemented("TODO")
