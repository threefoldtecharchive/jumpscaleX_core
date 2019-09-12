# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


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

    def _name_clean(self, name):
        name = name + ""
        name = name.replace(".", "_")
        if self._prefix:
            name = self._prefix + name
        return name

    def _add(self, name, value):
        name = self._name_clean(name)
        self._data[name] = value

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __delitem__(self, key):
        del self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getattr__(self, name):
        if name.startswith("_"):
            return self.__getattribute__(name)
        # don't clean here
        if name in self._data:
            return self._data[name]

        return self.__getattribute__(name)

    def __setattr__(self, name, value):
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

        print(j.core.tools.text_replace(out))

        return ""

    __str__ = __repr__
