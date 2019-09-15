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
        self._triggers = []
        # that way the triggers can know about this class and can call the triggers on this level
        # self._model._kosmosinstance = self

    def _init_post(self, **kwargs):
        self._inspect()  # force inspection
        self._protected = True

    def _bcdb_selector(self):
        """
        always uses the system BCDB, unless if this one implements something else
        it will go to highest parent it can find
        """
        if self._parent and self._parent._hasattr("_bcdb_selector"):
            return self._parent._bcdb_selector()
        return j.application.bcdb_system

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
                if "_SCHEMATEXT" in self.__class__.__dict__:
                    s = self.__class__._SCHEMATEXT
                elif "_SCHEMATEXT" in self.__class__._CHILDCLASS.__dict__:
                    s = self.__class__._CHILDCLASS._SCHEMATEXT
                else:
                    raise j.exceptions.JSBUG("cannot find _SCHEMATEXT on childclass or class itself")

            schema = j.data.schema.get_from_text(s)

            # if schema.url == "jumpscale.servers.gipc.process.1":
            #     from pudb import set_trace
            #
            #     set_trace()

            t2 = j.data.schema._schema_blocks_get(s)[0]

            t = self._process_schematext(t2)

            # if j.core.text.strip_to_ascii_dense(t) != j.core.text.strip_to_ascii_dense(s):
            #     from pudb import set_trace
            #
            #     set_trace()
            self._model_ = self._bcdb.model_get(schema=t)

            assert self._model_.schema._md5 == j.data.schema._md5(t)

            # if self._model_.schema._md5 != j.data.schema._md5(t2):
            #     from pudb import set_trace
            #
            #     set_trace()

            assert self._model_.schema._md5 in self._bcdb.meta._data["md5"]

        return self._model_

    def __init_class_post(self):

        if isinstance(j.baseclasses.object_config) and isinstance(j.baseclasses.object_config_collection):
            raise j.exceptions.Base("combination not allowed of config and configsclass")

    def _process_schematext(self, schematext):
        """
        rewrites the schema in such way there is always a parent_id and name
        :param schematext:
        :return:
        """
        assert schematext
        schematext = j.core.tools.text_strip(schematext, replace=False)
        if schematext.find("name") == -1:
            if "\n" != schematext[-1]:
                schematext += "\n"
            schematext += 'name** = ""\n'
        if self._mother_id_get():
            if schematext.find("mother_id") == -1:
                if "\n" != schematext[-1]:
                    schematext += "\n"
                schematext += "mother_id** = 0 (I)\n"

        return schematext

    #### NEED TO IMPLEMENT BUT THINK FIRST

    def _trigger_add(self, method):
        """

        triggers are called with (jsconfigs, jsconfig, action, propertyname=None)

        can register any method you want to respond on some change

        - jsconfigs: if relevant the factory starting drom model to 1 instance
        - jsconfig: the jsconfig object
        - action: e.g. new, delete, get, stop, ...  (any method call)
        - propertyname if the trigger was called because of change of the property of the data underneith

        return: jsconfig object
        """
        if method not in self._triggers:
            self._triggers.append(method)

    def _triggers_call(self, jsconfig, action=None):
        """
        will go over all triggers and call them with arguments given

        """
        assert isinstance(jsconfig, j.baseclasses.object_config)
        self._log_debug("trigger: %s:%s" % (jsconfig.name, action))
        for method in self._triggers:
            jsconfig = method(jsconfigs=self, jsconfig=jsconfig, action=action)
            assert isinstance(jsconfig, j.baseclasses.object_config)
        return jsconfig
