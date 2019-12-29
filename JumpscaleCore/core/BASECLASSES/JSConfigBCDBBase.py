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
from .JSBase import JSBase

"""
classes who use JSXObject for data storage but provide nice interface to enduser
"""

from .Attr import Attr


class JSConfigBCDBBase(JSBase, Attr):
    def _init_pre(self, **kwargs):
        self._model_ = None
        self._bcdb_ = None

        # self._model._kosmosinstance = self

    def _bcdb_selector(self):
        """
        always uses the system BCDB, unless if this one implements something else
        it will go to highest parent it can find
        """
        if self._parent and self._parent._hasattr("_bcdb_selector"):
            return self._parent._bcdb_selector()
        return j.data.bcdb.system

    @property
    def _bcdb(self):
        if not self._bcdb_:
            self._bcdb_ = self._bcdb_selector()
        return self._bcdb_

    @property
    def _model(self):
        if self._model_ is None:
            # self._log_debug("Get model for %s"%self.__class__._location)

            if isinstance(self, j.baseclasses.object_config):
                # can be from a parent
                if self._parent and isinstance(self._parent, j.baseclasses.object_config_collection):
                    self._model_ = self._parent._model
                    return self._model_

            if isinstance(self, j.baseclasses.object_config_base):
                if hasattr(self.__class__, "_SCHEMATEXT"):
                    s = self.__class__._SCHEMATEXT
                elif hasattr(self.__class__, "_CHILDCLASS") and "_SCHEMATEXT" in self.__class__._CHILDCLASS.__dict__:
                    s = self.__class__._CHILDCLASS._SCHEMATEXT
                else:
                    raise j.exceptions.JSBUG("cannot find _SCHEMATEXT on childclass or class itself")

            first = True
            for block in j.data.schema._schema_blocks_get(s):
                assert block
                if first:
                    # means this is the first block need to add it
                    has_mother = self._mother_id_get()
                    extrafields = {"name": "name** = (S)"}
                    if True or self._mother_id_get():  # TODO: will have to be resolved in future
                        extrafields["mother_id"] = "mother_id** = 0 (I)"
                    schema = j.data.schema.get_from_text(block, extrafields=extrafields)
                    first = False
                else:
                    j.data.schema.get_from_text(block)
            if first:
                raise j.exceptions.Input("didn't find schema's")

            if j.data.bcdb._master:
                self._model_ = self._bcdb.model_get(schema=schema)
            else:
                # make remote connection (to the threebotserver)
                self._model_ = j.clients.bcdbmodel.get(name=self._bcdb.name, schema=schema)
                self._bcdb_ = self._model.bcdb
            assert self._model_.schema._md5 == j.data.schema._md5(schema.text)

        return self._model_

    def __init_class_post(self):

        if isinstance(j.baseclasses.object_config) and isinstance(j.baseclasses.object_config_collection):
            raise j.exceptions.Base("combination not allowed of config and configsclass")

        return schematext, fieldsadded
