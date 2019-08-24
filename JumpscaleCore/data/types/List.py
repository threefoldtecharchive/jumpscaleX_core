"""Definition of several collection types (list, dict, set,...)"""

from Jumpscale import j
from Jumpscale.data.types.PrimitiveTypes import TypeBaseObjFactory, TypeBaseObjClass


from collections.abc import MutableSequence


class ListObject(TypeBaseObjClass, MutableSequence):
    def __init__(self, list_factory_type, values=[], child_type=None, model=None):
        """

        :param child_type: is the JSX basetype which is the child of the list, can be None, will be detected when required then

        """
        self._list_factory_type = list_factory_type
        self._inner_list = values
        self.__changed = False
        self._child_type_ = child_type
        self._current = 0
        self._model = model

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

    @_changed.setter
    def _changed(self, value):
        assert value == False  # only supported mode
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
        val = self._list_factory_type.clean(val, model=self._model)
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
        self._current = 0
        return self

    def __next__(self):
        if self._current + 1 > len(self._inner_list):
            raise StopIteration
        else:
            self._current += 1
            return self._inner_list[self._current - 1]

    def insert(self, index, value):
        if isinstance(value, j.data.schema._JSXObjectClass):
            self._inner_list.insert(index, self._child_type.clean(value, model=self._model))
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
        if isinstance(value, j.data.schema._JSXObjectClass):
            self._inner_list[index] = self._child_type.clean(value, model=self._model)
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

    def new(self, data=None):
        """
        return new subitem, only relevant when there are pointer_types used
        """

        data2 = self._child_type.clean(data, model=self._model)
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


class List(TypeBaseObjFactory):

    CUSTOM = True
    NAME = "list,l"

    def __init__(self, default=None):

        self.BASETYPE = "list"

        if isinstance(default, dict):  # means we have 2 levels to process
            subtype = default["subtype"]
            default = default["default"]
        else:
            subtype = None

        if not default or subtype == "o":
            self._default = []
        else:
            self._default = default

        if subtype:
            if subtype == "o" or "jsxobj" in subtype or subtype == "jsxobject":
                # need to take original default, but cannot store in obj, is for list of jsx objects
                self._SUBTYPE = j.data.types.get(subtype, default=default, cache=False)
            else:
                self._SUBTYPE = j.data.types.get(subtype)
        else:
            self._SUBTYPE = None

        if not isinstance(self._default, list) and not isinstance(self._default, set):
            self._default = self.clean(self._default)

    @property
    def SUBTYPE(self):
        if not self._SUBTYPE:
            if len(self._default) == 0:
                self._SUBTYPE = j.data.types.string
            else:
                if not self.list_check_1type(self._default):
                    raise j.exceptions.Value("default values need to be of 1 type")
                self._SUBTYPE = j.data.types.type_detect(self._default[0])
        return self._SUBTYPE

    def check(self, value):
        """Check whether provided value is a list"""
        return isinstance(value, (list, tuple, set)) or isinstance(value, ListObject)

    def list_check_1type(self, llist, die=True):
        if len(llist) == 0:
            return True
        ttype = j.data.types.type_detect(llist[0])
        for item in llist:
            res = ttype.check(item)
            if not res:
                if die:
                    raise j.exceptions.Value("List is not of 1 type.")
                else:
                    return False
        return True

    def toHR(self, val):
        val2 = self.clean(val)
        return val2.pylist(subobj_format="H")

    def toData(self, val=None):
        val2 = self.clean(val)
        if self.SUBTYPE.BASETYPE == "JSXOBJ":
            return [j.data.serializers.jsxdata.dumps(i) for i in val2]
        else:
            return val2._inner_list

    def clean(self, val=None, toml=False, sort=False, unique=False, ttype=None, model=None):

        if isinstance(val, ListObject):
            return val
        if val is None:
            val = self._default
        if ttype is None:
            ttype = self.SUBTYPE

        if j.data.types.int.check(val):
            val = [val]

        elif j.data.types.string.check(val):
            if val.strip("'\" []") in [None, ""]:
                return ListObject(self, [], ttype)
            val = [i.strip("[").strip("]") for i in val.split(",")]

        if val.__class__.__name__ in ["_DynamicListBuilder", "_DynamicListReader"]:
            val = [i for i in val]  # get binary data

        if not self.check(val):
            raise j.exceptions.Input("need list or set as input for clean on list")

        if len(val) == 0:
            return ListObject(self, [], ttype)

        res = []
        for item in val:
            if isinstance(item, str):
                item = item.strip().strip("'").strip('"')
            if toml:
                item = ttype.toml_string_get(item)
            else:
                item = ttype.clean(item)

            if unique:
                if item not in res:
                    res.append(item)
            else:
                res.append(item)
        if sort:
            res.sort()

        res = ListObject(self, res, ttype, model=model)

        return res

    def fromString(self, v, ttype=None):
        if ttype is None:
            ttype = self.SUBTYPE
        if v is None:
            v = ""
        if ttype is not None:
            ttype = ttype.NAME
        v = v.replace('"', "'")
        v = j.core.text.getList(v, ttype)
        v = self.clean(v)
        return v

    def toString(self, val, clean=True, sort=False, unique=False):
        """
        will translate to what we need in toml
        """
        if clean:
            val = self.clean(val, toml=False, sort=sort, unique=unique)
            val = val._inner_list
        if len(str(val)) > 30:
            # multiline
            out = ""
            for item in val:
                out += "%s,\n" % item
            out += "\n"
        else:
            out = ""
            for item in val:
                out += " %s," % item
            out = out.strip().strip(",").strip()
        return out

    def python_code_get(self, value, sort=False):
        """
        produce the python code which represents this value
        """
        value = self.clean(value, toml=False, sort=sort)
        out = "[ "
        for item in value:
            out += "%s, " % self.SUBTYPE.python_code_get(item)
        out = out.strip(",")
        out += " ]"
        return out

    def toml_string_get(self, val, key="", clean=True, sort=True):
        """
        will translate to what we need in toml
        """
        if clean:
            val = self.clean(val, toml=True, sort=sort)
        if key == "":
            raise NotImplemented()
        else:
            out = ""
            if len(str(val)) > 30:
                # multiline
                out += "%s = [\n" % key
                for item in val:
                    out += "    %s,\n" % item
                out += "]\n\n"
            else:
                out += "%s = [" % key
                for item in val:
                    out += " %s," % item
                out = out.rstrip(",")
                out += " ]\n"
        return out

    def toml_value_get(self, val, key=""):
        """
        will from toml string to value
        """
        if key == "":
            raise NotImplemented()
        else:
            return j.data.serializers.toml.loads(val)

    def capnp_schema_get(self, name, nr):
        # s = self.SUBTYPE.capnp_schema_get("name", 0)
        if self.SUBTYPE.BASETYPE is None:
            raise j.exceptions.bug("basetype of a jstype should not be None")
        if self.SUBTYPE.BASETYPE in ["string", "int", "float", "bool"]:
            capnptype = self.SUBTYPE.capnp_schema_get("", 0).split(":", 1)[1].rstrip(";").strip()
        else:
            # the sub type is now bytes because that is how the subobjects will
            # be stored
            capnptype = "Data"
        return "%s @%s :List(%s);" % (name, nr, capnptype)

    def __str__(self):
        out = "LIST TYPE:"
        if self._default != []:
            out += " - defaults: %s" % self.default_get()._inner_list
        if self.SUBTYPE:
            out += " - subtype: %s" % self.SUBTYPE.NAME
        return out

    __repr__ = __str__
