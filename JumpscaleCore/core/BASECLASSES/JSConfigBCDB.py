from Jumpscale import j
from .JSConfigBCDBBase import JSConfigBCDBBase

"""
classes who use JSXObject for data storage but provide nice interface to enduser
"""


class JSConfigBCDB(JSConfigBCDBBase):
    def _init_jsconfig(self, jsxobject=None, datadict=None, name=None, **kwargs):

        if jsxobject:
            self._data = jsxobject
        else:
            jsxobjects = []
            if name:
                jsxobjects = self._model.find(name=name)
            if len(jsxobjects) > 0:
                self._data = jsxobjects[0]
            else:
                self._data = self._model.new()  # create an empty object

        if datadict:
            assert isinstance(datadict, dict) or isinstance(datadict, j.baseclasses.dict)
            self._data_update(datadict)

        if name and self._data.name != name:
            self._data.name = name

    def _init_post(self, **kwargs):

        if not isinstance(self._model, j.clients.bcdbmodel._class) and self._data not in self._model.instances:
            self._model.instances.append(self._data)  # link from model to where its used
            # to check we are not creating multiple instances
            # assert id(j.data.bcdb.children.system.models[self._model.schema.url]) == id(self._model)

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
        jsxobjects = self._model.find(name=self.name)
        if len(jsxobjects) == 0:
            raise j.exceptions.JSBUG("cannot find obj:%s for reload" % self.name)
        self._data = jsxobjects[0]
        return self

    def _delete(self):
        assert self._model
        self._model.delete(self._data)
        if self._parent:
            if self._data.name in self._parent._children:
                if not isinstance(self._parent, j.baseclasses.factory):
                    # if factory then cannot delete from the mother because its the only object
                    del self._parent._children[self._data.name]
        self._children_delete()

    def save(self):
        self.save_()

    def save_(self):
        assert self._model
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
                "'%s' instance '%s' has been edited (changed)" % (self._parent.__jslocation__, self._data.name)
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
        return self._filter(filter=filter, llist=self._model.schema.propertynames)

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        out = "{BLUE}# JSXOBJ:{RESET}\n"
        ansi_out = j.core.tools.text_replace(out, die_if_args_left=False).rstrip()
        return ansi_out + "\n" + self._data.__repr__()
