from Jumpscale import j
from .JSXObjectBase import JSXObjectBase


class JSXObjectRoot(JSXObjectBase):
    def _init_pre(self, capnpdata=None, datadict=None, schema=None, model=None):

        self.id = None
        self._model = model
        self._root = self
        self.nid = 1

        self.acl_id = None
        self._acl = None

        return JSXObjectBase._init_pre(self, capnpdata=capnpdata, datadict=datadict, schema=schema)

    @property
    def _key(self):
        if hasattr(self, "name") and self.name:
            return "%s:%s" % (self._schema.url, self.name)
        elif hasattr(self, "id") and self.id:
            return "%s:%s" % (self._schema.url, self.id)
        else:
            return self._schema.url

    def Edit(self):
        if self._parent:
            raise j.exceptions.Base("cannot ask on subobj")
        e = j.data.dict_editor.get(self._ddict)
        e.edit()
        self._load_from_data(e._dict)

    def _view(self):
        if self._parent:
            raise j.exceptions.Base("cannot ask on subobj")
        e = j.data.dict_editor.get(self._ddict)
        e.view()

    @property
    def acl(self):
        if self._parent:
            raise j.exceptions.Base("cannot ask on subobj")
        if self._acl is None:
            if self.acl_id == 0:
                self._acl = self._model.bcdb.acl.new()
            else:
                self._acl = self._model.bcdb.acl
        return self._acl

    def save(self):
        if self._changed:

            self._capnp_obj  # makes sure we get back to binary form

            if self._model:
                if self._nosave:
                    obj, stop = self._model._triggers_call(obj=self, action="set_pre", propertyname=None)
                    return obj

                self.check_empty_indexed_fields()

                if not self._model._classname == "acl" and self._acl is not None:
                    if self.acl.id is None:
                        self.acl.save()
                    if self.acl.id != self.acl_id:
                        self._deserialized_items["ACL"] = True

                # SLOW, CANNOT DO LIKE THIS, THE INDEX ON SQLITE NEEDS TO PROTECT US HERE
                # # WE NEED UNIQUE PROPERTIES
                for prop_u in self._model.schema.properties_unique:
                    r = []
                    # find which properties need to be unique
                    # unique properties have to be indexed
                    args_search = {prop_u.name: getattr(self, prop_u.name)}
                    # WAS SUPER SLOW, CANNOT DO
                    # if "name" not in args_search:
                    #     for model in self._model.find():
                    #         m = getattr(model, prop_u.name)
                    #         if m == args_search[prop_u.name] and model.id != self.id:
                    #             msg = "could not save, was not unique.\n%s." % (args_search)
                    #             # can for sure not be ok
                    #             raise j.exceptions.Input(msg)
                    #
                    # else:
                    r = self._model.find(**args_search)
                    if len(r) > 1:
                        msg = "could not save, was not unique.\n%s." % (args_search)
                        # can for sure not be ok
                        raise j.exceptions.Input(msg)
                    elif len(r) == 1:
                        msg = "could not save, was not unique.\n%s." % (args_search)
                        if self.id and not self.id == r[0].id:
                            raise j.exceptions.Input(msg)

                obj = self._model.set(self)
                assert obj.id
                self.id = obj.id

                return obj

            self._changed = False

            return self

    def delete(self):

        if self._model:
            self._model._triggers_call(obj=self, action="delete", propertyname=None)
            if self._nosave:
                return
            if self._readonly:
                raise j.exceptions.Base("object _readonly, cannot be saved.\n%s" % self)
            if not self._model.__class__.__name__ == "ACL":
                self._model.delete(self)

        self._capnp_obj_ = self._capnp_schema.new_message()

        self._reset()  # remove all dangling children & _deserialized_items

        self._capnp_obj
        self._deserialized_items = {}
        self._changed_deserialized_items = False
        self._defaults_set()
        self.id = None

    def stop(self):
        # will be called when BCDB stops, if changes will save
        try:
            self.save()
        except:
            # can fail because obj empty and index cannot be saved because of it, need to do this better
            pass
        pass  # TODO: for later
