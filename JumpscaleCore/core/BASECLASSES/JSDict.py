from Jumpscale import j

from collections.abc import MutableMapping


class JSDict(MutableMapping):
    def __init__(self, data=(), name=None, prefix=None):
        self._name = name
        self._data = {}
        self._prefix = prefix
        self.update(data)

    @property
    def _values_iterator(self):
        for item in self._data.values():
            yield item

    # def _name_clean(self, name):
    #     name = name + ""
    #     name = name.replace(".", "_")
    #     if self._prefix:
    #         name = self._prefix + name
    #     return name

    def _add(self, name, value):
        # TODO: we should not use this
        name = name.replace("__", ".")
        self._data[name] = value

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        key = key.replace("__", ".")
        return self._data[key]

    def __delitem__(self, key):
        key = key.replace("__", ".")
        del self._data[key]

    def __setitem__(self, key, value):
        key = key.replace("__", ".")
        self._data[key] = value

    def __getattr__(self, name):
        name = name.replace("__", ".")
        if name.startswith("_"):
            return self.__getattribute__(name)
        # don't clean here
        if name in self._data:
            return self._data[name]

        return self.__getattribute__(name)

    def __setattr__(self, name, value):
        name = name.replace("__", ".")
        if name.startswith("_"):
            self.__dict__[name] = value
            return

        raise j.exceptions.Base("protected property:%s" % name)

    def __repr__(self):
        if self._name:
            out = "{BLUE} # dict %s:{GRAY}\n\n" % self._name
        else:
            out = "{BLUE} # dict: \n\n{GRAY}"

        for key, val in self._data.items():
            try:
                r = str(val)
            except:
                r = ""
            if r and len(r) < 50:
                out += " - %s : %s\n" % (key, r.replace("\n", ""))
            else:
                out += " - %s\n" % key

        out += "{RESET}"

        return j.core.tools.text_replace(out)

    __str__ = __repr__
