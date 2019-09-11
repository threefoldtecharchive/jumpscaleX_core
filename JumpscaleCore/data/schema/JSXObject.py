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


class JSXObject(j.baseclasses.object):
    def _init_pre(self, capnpdata=None, datadict={}, schema=None, model=None):
        self._capnp_obj_ = None
        self.id = None

        if model:
            self._model = model
            self._schema_ = schema
        else:
            self._schema_ = schema
            self._model = None
            assert model == None

        self._deserialized_items = {}

        self._autosave = False

        self.acl_id = None
        self._acl = None

        self._load_from_data(capnpdata=capnpdata)  # ONLY LOADS THE self._capnp_obj_
        if datadict:
            self._data_update(datadict)

        # self.nid = 1

        self._logger_enable()

    @property
    def _schema(self):
        if self._schema_:
            return self._schema_
        else:
            return self._model.schema

    @property
    def _key(self):
        if hasattr(self, "id") and self.id:
            return "%s:%s" % (self._schema.url, self.id)
        else:
            return self._schema.url

    @property
    def _readonly(self):
        if self._model:
            return self._model.readonly
        return False

    @property
    def _nosave(self):
        if self._model:
            return self._model.nosave
        return False

    @property
    def _capnp_schema(self):
        return self._schema._capnp_schema

    def _data_update(self, datadict):
        if not isinstance(datadict, dict):
            raise j.exceptions.Base("need to be dict, was:\n%s" % datadict)
        if self._model is not None:
            data = self._model._dict_process_in(datadict)
        for key, val in datadict.items():
            try:
                setattr(self, key, val)
            except Exception as e:
                if isinstance(e, ValueError):
                    msg = "cannot update data for: %s  set prop %s with '%s'" % (self._schema.url, key, val)
                    e.args = (msg,)
                raise e

    def _load_from_data(self, capnpdata=None):
        """
        THIS ERASES EXISTING DATA !!!

        :param data: can be binary (capnp), str=json, or dict
        :return:
        """

        if isinstance(capnpdata, bytes):
            self._capnp_obj_ = self._capnp_schema.from_bytes_packed(capnpdata)
            set_default = False
        else:
            self._capnp_obj_ = self._capnp_schema.new_message()
            set_default = True
            self.acl_id = 0
            self._acl = None

        if set_default:
            self._defaults_set()  # only do when new message

    def Edit(self):
        e = j.data.dict_editor.get(self._ddict)
        e.edit()
        self._load_from_data(e._dict)

    def _view(self):
        e = j.data.dict_editor.get(self._ddict)
        e.view()

    @property
    def acl(self):
        if self._acl is None:
            if self.acl_id == 0:
                self._acl = self._model.bcdb.acl.new()
        return self._acl

    def _hr_get(self, exclude=[]):
        """
        human readable test format
        """
        out = "\n"
        res = self._ddict_hr_get(exclude=exclude)
        keys = [name for name in res.keys()]
        keys.sort()
        for key in keys:
            item = res[key]
            out += "- %-30s: %s\n" % (key, item)
        return out

    def save(self, serialize=False):
        if self._changed:
            self._capnp_obj  # makes sure we get back to binary form
            if serialize:
                self._deserialized_items = {}  # need to go back to smallest form
        if self._model:
            if not self._model._classname == "acl" and self._acl is not None:
                if self.acl.id is None:
                    self.acl.save()
                if self.acl.id != self.acl_id:
                    self._deserialized_items["ACL"] = True

            if self._changed:

                # WE NEED UNIQUE PROPERTIES
                for prop_u in self._model.schema.properties_unique:
                    r = []
                    # find which properties need to be unique
                    # unique properties have to be indexed
                    args_search = {prop_u.name: getattr(self, prop_u.name)}
                    if "name" not in args_search:
                        for model in self._model.find():
                            m = getattr(model, prop_u.name)
                            if m == args_search[prop_u.name] and model.id != self.id:
                                msg = "could not save, was not unique.\n%s." % (args_search)
                                # can for sure not be ok
                                raise j.exceptions.Input(msg)

                    else:
                        r = self._model.find(**args_search)
                    if len(r) > 1:
                        msg = "could not save, was not unique.\n%s." % (args_search)
                        # can for sure not be ok
                        raise j.exceptions.Input(msg)
                    elif len(r) == 1:
                        msg = "could not save, was not unique.\n%s." % (args_search)
                        if self.id:
                            if not self.id == r[0].id:
                                # j.shell()
                                raise j.exceptions.Input(msg)
                        else:
                            self.id = r[0].id
                            self._ddict_hr  # to trigger right serialization
                            if self._data == r[0]._data:
                                return self  # means data was not changed
                            else:  # means data is not the same
                                self.id = None
                                raise j.exceptions.Input(msg)

                if not self._nosave:
                    o = self._model.set(self)
                    self.id = o.id

                obj = self._model._triggers_call(obj=self, action="save", propertyname=None)

                return obj
            return self

        raise j.exceptions.Base("cannot save, model not known")

    def delete(self):
        if self._model:
            self._model._triggers_call(obj=self, action="delete", propertyname=None)
            if self._nosave:
                return
            if self._readonly:
                raise j.exceptions.Base("object _readonly, cannot be saved.\n%s" % self)
            if not self._model.__class__.__name__ == "ACL":
                self._model.delete(self)
            return self

        raise j.exceptions.Base("cannot save, model not known")

    def _check(self):
        self._ddict
        return True

    @property
    def _data(self):
        self._capnp_obj  # leave, is to make sure we have error if something happens
        return j.data.serializers.jsxdata.dumps(self)

    @property
    def _ddict_hr(self):
        """
        human readable dict
        """
        d = self._ddict_hr_get(ansi=False)
        return d

    @property
    def _ddict_json_hr(self):
        """
        json readable dict
        """
        return j.data.serializers.json.dumps(self._ddict_hr)

    @property
    def _json(self):
        return j.data.serializers.json.dumps(self._ddict)  # DO NOT USE THE HR ONE

    @property
    def _toml(self):
        return j.data.serializers.toml.dumps(self._ddict)

    @property
    def _msgpack(self):
        return j.data.serializers.msgpack.dumps(self._ddict)

    def __eq__(self, val):
        if isinstance(val, str) or isinstance(val, int) or isinstance(val, float) or isinstance(val, set):
            return False
        if not isinstance(val, JSXObject):
            tt = j.data.types.get("jsxobject", self._schema.url)
            val = tt.clean(val)
        return self._data == val._data

    def __hash__(self):
        return hash(j.data.hash.md5_string(self._data))

    def __repr__(self):
        # FIXME: breaks in some cases in docsites generation needs to be cleanly implemented
        out = self._str_get(ansi=True)
        # # #TODO: *1 when returning the text it does not represent propertly, needs to be in kosmos shell I think
        # # IS UGLY WORKAROUND
        print(out)
        return ""

    def __str__(self):
        out = self._str_get(ansi=False)
        return out
