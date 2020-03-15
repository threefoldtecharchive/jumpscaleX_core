from collections.abc import MutableSequence


class JSList(MutableSequence):
    def __init__(self, list_factory_type, values=None, child_type=None, model=None, parent=None):
        """

        :param child_type: is the JSX basetype which is the child of the list, can be None, will be detected when required then

        """
        self._list_factory_type = list_factory_type
        self._inner_list = values or []
        self.__changed = False
        self._child_type_ = child_type
        self._current = 0
        self._model = model
        self.__parent = parent
        current = self
        while current._parent:
            current = current._parent
        self._root = current

    @property
    def isjsxobject(self):
        return self._list_factory_type.SUBTYPE.BASETYPE == "JSXOBJ"

    @property
    def _changed(self):
        if self.__changed:
            return self.__changed
        for item in self._inner_list:
            # need to check if underlying jsxobjexts got changed?
            if isinstance(item, j.data.schema._JSXObjectClass):
                if item._changed:
                    self.__changed = True
                    return True
        return False

    def serialize(self):
        for item in self._inner_list:
            if isinstance(item, j.data.schema._JSXObjectClass):
                item.serialize()

    @_changed.setter
    def _changed(self, value):
        if value == False:
            # need to make sure the objects (list(jsxobj) or jsxobj need to set their state to changed)
            for item in self._inner_list:
                # need to check if underlying jsxobjexts will change their change state
                if isinstance(item, j.data.schema._JSXObjectClass):
                    item._changed = False
        self.__changed = False

    def __len__(self):
        """
        get length of list
        """
        return len(self._inner_list)

    def __eq__(self, val):
        if self.isjsxobject:
            val = self._list_factory_type.clean(val, model=self._model, parent=self.__parent)
        else:
            val = self._list_factory_type.clean(val)
        return val._inner_list == self._inner_list

    def __delitem__(self, index):
        """
        delete the item using index of collections
        """

        self._inner_list.__delitem__(index)
        self.__changed = True

    @property
    def value(self):
        return self._inner_list

    @property
    def _datadict(self):
        res = []
        for item in self._inner_list:
            if isinstance(item, j.data.schema._JSXObjectClass):
                res.append(item._ddict)
            else:
                res.append(item)
        return res

    def __iter__(self):
        return iter(self._inner_list)

    def insert(self, index, value):
        if self.isjsxobject:
            self._inner_list.insert(index, self._child_type.clean(value, model=self._model, parent=self.__parent))
        else:
            self._inner_list.insert(index, self._child_type.clean(value))
        self.__changed = True

    def __setitem__(self, index, value):
        """
        insert value in specific index in collections
        Arguments:
            index : location in collections
            value : value that add in collections
        """
        if self.isjsxobject:
            self._inner_list[index] = self._child_type.clean(value, model=self._model, parent=self.__parent)
        else:
            self._inner_list[index] = self._child_type.clean(value)
        self.__changed = True

    def __getitem__(self, index):
        """
        get item from list using index
        """

        return self._inner_list.__getitem__(index)

    def pylist(self, subobj_format="D"):
        """
        python clean list

        :param subobj_format
        +--------------------+--------------------+-----------------------------------------------------------------------------------+
        |     value          |     Description    |                example                                                            |
        +--------------------+--------------------+-----------------------------------------------------------------------------------+
        |       J            |     DDICT_JSON     | ['{\n"valid": false,\n"token_price": "\\u00000\\u0005\\u0000\\u0000\\u0000"\n}']  |
        |       D            |     DDICT          | [{'valid': False, 'token_price': b'\x000\x05\x00\x00\x00'}]                       |
        |       H            |     DDict_HR       | [{valid': False, 'token_price': '5 EUR'}]                                         |
        +--------------------+--------------------+-----------------------------------------------------------------------------------+
        """
        res = []
        for item in self._inner_list:

            if isinstance(item, j.data.schema._JSXObjectClass):
                if subobj_format == "J":
                    res.append(item._ddict_json)
                elif subobj_format == "D":
                    res.append(item._ddict)
                elif subobj_format == "H":
                    res.append(item._ddict_hr)
                else:
                    raise j.exceptions.Value("only support type J,D,H")
            else:
                if subobj_format == "H":
                    res.append(self._child_type.toHR(item))
                elif subobj_format == "J":
                    res.append(self._child_type.toJSON(item))
                elif subobj_format == "D":
                    res.append(self._child_type.toData(item))
                else:
                    raise j.exceptions.Value("only support type J,D,H")
        return res

    def new(self, data=None, **kwargs):
        """
        return new subitem, only relevant when there are pointer_types used
        """
        if self.isjsxobject:
            if kwargs:
                data = kwargs
            data2 = self._child_type.clean(data, model=self._model, parent=self.__parent)
        else:
            data2 = self._child_type.clean(data)
        self.append(data2)
        self.__changed = True
        return data2

    @property
    def _child_type(self):
        """
        :return: jumpscale type
        """
        if self._child_type_ is None:
            if len(self._inner_list) == 0:
                raise j.exceptions.Value("cannot auto detect which type used in the list")
            type1 = j.data.types.list.list_check_1type(self._inner_list)
            if not type1:
                raise j.exceptions.Value("cannot auto detect which type used in the list, found more than 1 type")
            self._child_type_ = j.data.types.type_detect(self._inner_list[0])
        return self._child_type_

    def __repr__(self):
        out = ""
        for item in self.pylist(subobj_format="H"):
            if isinstance(item, dict):
                out += "%s" % j.core.text.indent(j.data.serializers.toml.dumps(item))
            else:
                out += "- %s\n" % item
        if out.strip() == "":
            return "[]"
        return out

    __str__ = __repr__
