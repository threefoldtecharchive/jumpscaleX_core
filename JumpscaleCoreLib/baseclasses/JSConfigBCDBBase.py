from Jumpscale import j
from .JSBase import JSBase

"""
classes who use JSXObject for data storage but provide nice interface to enduser
"""

from .JSAttr import Attr


class JSConfigBCDBBase(JSBase, Attr):
    def _init_pre(self, **kwargs):
        self._model_ = None
        self._bcdb_ = None
        self._schema_ = None

    def _bcdb_selector(self):
        """
        always uses the system BCDB, unless if this one implements something else
        it will go to highest parent it can find
        """
        if self.__parent and self.__parent._hasattr("_bcdb_selector"):
            return self.__parent._bcdb_selector()
        return j.data.bcdb.system

    @property
    def _bcdb(self):
        if not self._bcdb_:
            self._bcdb_ = self._bcdb_selector()
        return self._bcdb_

    @property
    def _schema(self):
        if not self._schema_:
            self._schema_ = self._model.schema
        return self._schema_

    @property
    def _model(self):

        if self._model_ in [None, False]:

            # self._log_debug("Get model for %s"%self.__class__._location)

            if isinstance(self, j.baseclasses.object_config):
                # can be from a parent
                if self.__parent and isinstance(self.__parent, j.baseclasses.object_config_collection):
                    self._model_ = self.__parent._model
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
                    schema = j.data.schema.get_from_text(block, newest=True)
                    if self._model_ != False:
                        has_mother = self._mother_id_get()
                        if "name" not in schema.props:
                            raise j.exceptions.Input("name not found in schema", data=schema.text)
                        if not schema.props["name"].index:
                            raise j.exceptions.Input("name need to be a field and index (**)", data=schema)
                        if has_mother:
                            if "mother_id" not in schema.props:
                                raise j.exceptions.Input(
                                    "mother_id need to be a field (int) and indexed, didn't exist", data=schema.text
                                )
                            if not schema.props["mother_id"].index:
                                raise j.exceptions.Input(
                                    "mother_id need to be a field (int) and index (**)", data=schema.text
                                )
                    first = False
                else:
                    j.data.schema.get_from_text(block, newest=True)
            if first:
                raise j.exceptions.Input("didn't find schema's")

            if self._model_ is False:
                self._bcdb_ = False
                self._schema_ = schema
            else:
                if j.data.bcdb._master:
                    self._model_ = self._bcdb.model_get(schema=schema)
                else:
                    # make remote connection (to the threebotserver)
                    # print("CONNECT TO THREEBOTSERVER FOR MODEL")
                    self._model_ = j.clients.bcdbmodel.get(name=self._bcdb.name, schema=schema)
                    self._bcdb_ = self._model.bcdb

        return self._model_

    def __init_class_post(self):

        if isinstance(j.baseclasses.object_config) and isinstance(j.baseclasses.object_config_collection):
            raise j.exceptions.Base("combination not allowed of config and configsclass")

        return schematext, fieldsadded
