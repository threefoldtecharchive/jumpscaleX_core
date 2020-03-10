from TypeBaseClassesObj import TypeBaseObjClass


class TypeBaseClass:
    __ALIAS = None
    __NAME = None
    __DEFAULT = None

    def toString(self, v):
        """
        string representation, can go to string & back
        """
        return str(self.clean(v))

    def toHR(self, v):
        """
        human readable tsring implementatiokn
        """
        return self.toString(v)

    def toDict(self, v):
        """
        to dict representation
        """
        raise NotImplemented()

    def toDictHR(self, v):
        """
        to dict and put human readable items inside
        does not guarantee to be able to go back
        """
        raise NotImplemented()

    def toData(self, v):
        """
        serialize to a data format
        :param v:
        :return:
        """
        o = self.clean(v)
        if isinstance(o, TypeBaseObjClass):
            data = o._datadict
        else:
            data = o
        return data

    def check(self, value):
        """
        - if there is a specific implementation e.g. string, float, enumeration, it will check if the input is that implementation
        - if not strict implementation or we cannot know e.g. an address will return None
        """
        if hasattr(self, "NOCHECK") and self.NOCHECK is True:
            return RuntimeError("check cannot be used")
        raise j.exceptions.Value("not implemented")

    def possible(self, value):
        """
        will check if it can be converted to the jumpscale representation, basically the clean works without error
        :return:
        """
        try:
            self.clean(str(value))
            return True
        except Exception as e:
            return False

    def default_get(self):
        if self._default is None:
            raise j.exceptions.Value("self._default cannot be None")
        return self.clean(self._default)

    def clean(self, value, parent=None):
        """
        """
        raise j.exceptions.Value("not implemented")

    def python_code_get(self, value):
        """
        produce the python code which represents this value
        """
        value = self.clean(value)
        return "'%s'" % value

    def toml_string_get(self, value, key=""):
        """
        will translate to what we need in toml
        """
        if key == "":
            return "'%s'" % (self.clean(value))
        else:
            return "%s = '%s'" % (key, self.clean(value))

    def capnp_schema_get(self, name, nr):
        return "%s @%s :Text;" % (name, nr)
