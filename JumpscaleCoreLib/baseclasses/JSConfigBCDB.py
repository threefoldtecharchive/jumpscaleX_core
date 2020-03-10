from Jumpscale import j
from .JSConfigBCDBBase import JSConfigBCDBBase

"""
classes who use JSXObject for data storage but provide nice interface to enduser
"""


class JSConfigBCDB(JSConfigBCDBBase):
    def _init_jsconfig(self, jsxobject=None, datadict=None, name=None, **kwargs):

        if name:
            if jsxobject and not jsxobject.name:
                jsxobject.name = name
        elif jsxobject != None and jsxobject.name:
            pass
        else:
            raise j.exceptions.Input("Please specify name and cannot be empty, or jsxobject")

        if jsxobject:
            self._data = jsxobject
        else:
            jsxobjects = []

            if name and not self._bcdb_ == False and not self._model_ == False:
                jsxobjects = self._model.find(name=name)

            if len(jsxobjects) > 1:
                raise j.exceptions.JSBUG("there should never be more than 1 record with same name:%s" % name)
            elif len(jsxobjects) == 1:
                self._data = jsxobjects[0]
                # self._model
            else:
                self._model  # make sure model has been resolved
                if self._model == False:
                    # and hasattr(self, "_schema_")
                    self._data = self._schema.new()  # create an empty object
                else:
                    self._data = self._model.new()  # create an empty object

        if kwargs:
            if not datadict:
                datadict = {}
            datadict.update(kwargs)

        if datadict:
            assert isinstance(datadict, dict) or isinstance(datadict, j.baseclasses.dict)
            self._data_update(datadict)

        if name and self._data.name != name:
            self._data.name = name

        assert self._data.name

        if self._model and self._data.id == None:
            # means there is a model and id not set yet, we need to save
            self._data.save()
        assert self.id

        if "autosave" in kwargs:
            self._data._autosave = j.data.types.bool.clean(kwargs["autosave"])

    def _init_jsconfig_post(self, **kwargs):

        if (
            not isinstance(self._model, j.clients.bcdbmodel._class)
            and self._model
            and self._data not in self._model.instances
        ):
            self._model.instances.append(self._data)  # link from model to where its used
            # to check we are not creating multiple instances
            # assert id(j.data.bcdb.children.system.models[self._model.schema.url]) == id(self._model)

    @property
    def _autosave(self):
        return self._data._autosave

    @property
    def name(self):
        return self._data.name

    @property
    def _key(self):
        assert self.name
        return self._classname + "_" + self.name

    @property
    def _name(self):
        assert self._classname
        return self._classname

    @property
    def _id(self):
        return self._data.id

    @property
    def id(self):
        return self._data.id

    def _data_update(self, datadict):
        """
        will not automatically save the data, don't forget to call self.save()

        :param kwargs:
        :return:
        """
        # ddict = self._data._ddict  # why was this needed? (kristof)
        self._data._data_update(datadict=datadict)

    def delete(self):
        """
        :return:
        """
        self._delete()

    def load(self):
        """
        load from bcdb
        :return:
        """
        if not self._model:
            return self
        jsxobjects = self._model.find(name=self.name)
        if len(jsxobjects) == 0:
            raise j.exceptions.JSBUG("cannot find obj:%s for reload" % self.name)
        self._data = jsxobjects[0]
        return self

    def _delete(self):
        if not self._model:
            return
        self._model.delete(self._data)
        if self.__parent:
            if self._data.name in self.__parent._children:
                if not isinstance(self.__parent, j.baseclasses.factory):
                    # if factory then cannot delete from the mother because its the only object
                    del self.__parent._children[self._data.name]
        self.__children_delete()

    def save(self):
        self.save_()

    def save_(self):
        if not self._model:
            return
        mother_id = self._mother_id_get()
        if mother_id:
            # means there is a mother
            self._data.mother_id = mother_id
            assert self._data._model.schema._md5 == self._model.schema._md5

        self._data.save()

    def edit(self):
        """

        edit data of object in editor
        chosen editor in env var: "EDITOR" will be used

        :return:

        """
        path = j.core.tools.text_replace("{DIR_TEMP}/js_baseconfig_%s.toml" % self.__class__._location)
        data_in = self._data._toml
        j.sal.fs.writeFile(path, data_in)
        j.core.tools.file_edit(path)
        data_out = j.sal.fs.readFile(path)
        if data_in != data_out:
            self._log_debug(
                "'%s' instance '%s' has been edited (changed)" % (self.__parent.__jslocation__, self._data.name)
            )
            data2 = j.data.serializers.toml.loads(data_out)
            self._data.data_update(data2)
        j.sal.fs.remove(path)

    def _dataprops_names_get(self, filter=None):
        """
        e.g. in a JSConfig object would be the names of properties of the jsxobject = data
        e.g. in a JSXObject would be the names of the properties of the data itself

        :return: list of the names
        """
        return self._filter(filter=filter, llist=self._schema_.propertynames)

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        # out = "{BLUE}# JSXOBJ:{RESET}\n"
        out = "{RESET}\n"
        ansi_out = j.core.tools.text_replace(out, die_if_args_left=False).rstrip()
        return ansi_out + "\n" + self._data.__repr__()
