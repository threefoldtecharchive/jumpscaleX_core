from Jumpscale import j

### CLASS DEALING WITH THE ATTRIBUTES SET & GET


class Attr:
    def _init_post_attr(self, **kwargs):
        self._inspect()
        self._protected = True

    def __getattr__(self, name):
        # if private or non child then just return
        name = name.replace("__", ".")
        if not name.startswith("_"):

            child = self._validate_child(name)
            if child:
                return child

            if isinstance(self, j.baseclasses.object_config):
                if name in self._model.schema.propertynames:
                    return self._data.__getattribute__(name)

            if isinstance(self, j.baseclasses.object_config_base):

                if (
                    name.startswith("_")
                    or name in self._methods
                    or name in self._properties
                    or name in self._dataprops_names_get()
                ):
                    return self.__getattribute__(name)  # else see if we can from the factory find the child object

                if isinstance(self, j.baseclasses.object_config_collection):
                    r = self._get(name=name, die=False)
                    if not r:
                        raise j.exceptions.NotFound(
                            "try to get attribute: '%s', instance did not exist, was also not a method or property, was on '%s'"
                            % (name, self._key)
                        )
                    return r

        try:
            r = self.__getattribute__(name)
        except AttributeError as e:
            # whereami = self._key
            msg = "could not find attribute:%s (error was:%s)" % (name, e)
            raise j.exceptions.NotFound(msg)

        return r

    def __setattr__(self, name, value):

        if name.startswith("_"):
            self.__dict__[name] = value
            return

        if isinstance(self, j.baseclasses.object_config):

            if name == "data":
                raise j.exceptions.Base("protected property:%s" % name)

            if "_data" in self.__dict__ and name in self._model.schema.propertynames:
                # self._log_debug("SET:%s:%s" % (name, value))
                self._data.__setattr__(name, value)
                return

        if not self._protected or name in self._properties:
            self.__dict__[name] = value
        else:
            raise j.exceptions.Base("protected property:%s" % name)
