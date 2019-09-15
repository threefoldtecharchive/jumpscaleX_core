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

### CLASS DEALING WITH THE ATTRIBUTES SET & GET


class Attr:
    def _init_post_attr(self, **kwargs):
        self._protected = True

    def __getattr__(self, name):
        # if private or non child then just return

        if not name.startswith("_"):

            if name in self._children:
                return self._children[name]

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
                    rc, r = self._get(name=name, die=False)
                    if not r:
                        raise j.exceptions.NotFound(
                            "try to get attribute: '%s', instance did not exist, was also not a method or property, was on '%s'"
                            % (name, self._key)
                        )
                    return r

        try:
            r = self.__getattribute__(name)
        except AttributeError as e:
            whereami = self._key
            msg = "could not find attribute:%s in %s (error was:%s)" % (name, whereami, e)
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
                # if value != self._data.__getattribute__(name):
                # self._log_debug("SET:%s:%s" % (name, value))
                self._data.__setattr__(name, value)
                return

        if not self._protected or name in self._properties:
            self.__dict__[name] = value
        else:
            raise j.exceptions.Base("protected property:%s" % name)
