from Jumpscale import j

### CLASS DEALING WITH THE ATTRIBUTES SET & GET


class JSAttr:
    def _init_attr(self, **kwargs):
        self._inspect()  # can always inspect
        self._protected = True

    def __getattr__(self, name):
        if not name.startswith("_"):
            # child = self._validate_child(name)
            # if child:
            #     return child
            if name in self.__properties:
                __property_state
                return self.__getattribute__(name)

        return self.__getattribute__(name)
        # except AttributeError as e:
        #     # whereami = self._key
        #     msg = "could not find attribute:%s (error was:%s)" % (name, e)
        #     raise AttributeError(msg)

    def __setattr__(self, name, value):

        if name.startswith("_"):
            self.__dict__[name] = value
            return

        if isinstance(self, j.baseclasses.object_config):

            if name == "data":
                raise j.exceptions.Base("protected property:%s" % name)

            if "_data" in self.__dict__ and name in self._schema.propertynames:
                # self._log_debug("SET:%s:%s" % (name, value))
                self._data.__setattr__(name, value)
                return

        if not self._protected or name in self._properties:
            self.__dict__[name] = value
        else:
            raise j.exceptions.Base("protected property:%s" % name)
