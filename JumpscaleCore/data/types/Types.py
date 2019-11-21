"""Definition of several primitive type properties (integer, string,...)"""
from Jumpscale import j
from .AdvTypes import *
from .CollectionTypes import *
from .PrimitiveTypes import *
from .Enumeration import Enumeration
from .IPAddress import *
from .JSXObjectTypeFactory import JSXObjectTypeFactory
from .List import *

import copy


class Types(j.baseclasses.object, j.baseclasses.testtools):

    __jslocation__ = "j.data.types"

    def _init(self, **kwargs):
        self._types_list = [
            List,
            Dictionary,
            Guid,
            Path,
            Boolean,
            Integer,
            Float,
            String,
            Bytes,
            StringMultiLine,
            IPRange,
            IPPort,
            Tel,
            YAML,
            MSGPACK,
            JSON,
            Email,
            Date,
            DateTime,
            Duration,
            Numeric,
            Percent,
            Set,
            CapnpBin,
            JSXObjectTypeFactory,
            Url,
            Enumeration,
            IPAddress,
        ]

        self._TypeBaseObjClass = TypeBaseObjClass
        self._TypeBaseClassUnserialized = TypeBaseClassUnserialized

        self._type_check_list = []
        self._aliases = {}

        for typeclass in self._types_list:
            name = typeclass.NAME.strip().strip("_").lower()
            if "," in name:
                aliases = [name.strip() for name in name.split(",")]
                name = aliases[0]
                aliases.pop(aliases.index(name))
            else:
                aliases = None
            name = name.split(",")[0].strip()

            o = self.__attach(name, typeclass)
            if name in self._type_check_list:
                raise j.exceptions.Value("there is duplicate type:%s" % name)
            if not hasattr(o, "NOCHECK") or o.NOCHECK is False:
                if not hasattr(typeclass, "CUSTOM") or typeclass.CUSTOM is False:
                    self._type_check_list.append(name)
            if aliases:
                for alias in aliases:
                    self._aliases[alias] = name

        self._types = {}

        self.list = List()

    def __attach(self, name, typeclass):
        name = name.strip().lower()
        name2 = "_%s" % name
        typeclass.NAME = name
        self.__dict__[name2] = typeclass  # attach class

        if not hasattr(typeclass, "CUSTOM") or typeclass.CUSTOM is False:
            o = typeclass()
            o._jsx_location = "j.data.types.%s" % name
            self.__dict__[name] = o

            return o

    def type_detect(self, val):
        """
        check for most common types
        """
        for key in self._type_check_list:
            ttype = self.__dict__[key]
            if ttype.check(val):
                return ttype
        raise j.exceptions.Value("did not detect val for :%s" % val)

    def get(self, ttype, default=None, cache=True):
        """

        mytype = j.data.types.get("s") #will return string type (which is a primitive type)  !!!TYPES!!!

        type is one of following

        - s, str, string
        - bytes
        - i, int, integer
        - f, float
        - b, bool,boolean
        - tel, mobile
        - d, date
        - t, datetime
        - n, numeric
        - h, set       #set of 2 int
        - p, percent
        - o, jsxobject
        - ipaddr, ipaddress
        - ipport, tcpport
        - iprange
        - email
        - multiline
        - list
        - dict
        - yaml
        - guid
        - url
        - e, enum        #enumeration
        - a, acl
        - u, user
        - g, group
        - json
        - yaml
        - msgpack

        !!!TYPES!!!

        :param default: e.g. "red,blue,green" for an enumerator
            for certain types e.g. enumeration the default value is needed to create the right type

        """

        ttype = ttype.lower().strip()

        if ttype != "list" and ttype.startswith("l"):
            default = {"default": default, "subtype": ttype[1:]}
            ttype = "list"

        # check if there is an alias
        if ttype in self._aliases:
            ttype = self._aliases[ttype]

        klasstype = "_%s" % ttype
        if klasstype not in self.__dict__:
            raise j.exceptions.Value("did not find type class:%s" % klasstype)
        tt_class = self.__dict__[klasstype]  # is the class

        if default:
            # key0=default_copy.replace(" ","").replace(",","_").replace("[","").replace("]","").replace("\"","")
            key0 = j.data.hash.md5_string(str(default))
            key = "%s_%s" % (tt_class.NAME, key0)
        else:
            if ttype not in self.__dict__:
                raise j.exceptions.RuntimeError("did not find type:'%s'" % ttype)
            return self.__dict__[ttype]

        if cache and key in self._types:
            return self._types[key]

        tt = tt_class(default=default)
        tt._jsx_location = "j.data.types._types['%s']" % key

        # #not sure this is the right way (despiegk)
        # if ttype.startswith("l"):
        #     #is a list, copy default values in
        #     tt._default_values = tt.clean(default_copy)._inner_list #make sure they are clean

        self._types[key] = tt

        return self._types[key]

    def test(self, name=""):
        """
        kosmos 'j.data.types.test()'

        if want run specific test ( write the name of test ) e.g. j.data.schema.test(name="base")
        """
        self._test_run(name=name)

    def fix(self, val, default):
        """
        will convert val to type of default

        separated string goes to [] if default = []

        BE CAREFULL THIS IS A SLOW PROCESS, USE CAREFULLY

        """
        if val is None or val == "" or val == []:
            return default

        if j.data.types.list.check(default):
            res = []
            if j.data.types.list.check(val):
                for val0 in val:
                    if val0 not in res:
                        res.append(val0)
            else:
                val = str(val).replace("'", "")
                if "," in val:
                    val = [item.strip() for item in val.split(",")]
                    for val0 in val:
                        if val0 not in res:
                            res.append(val0)
                else:
                    if val not in res:
                        res.append(val)
        elif j.data.types.bool.check(default):
            if str(val).lower() in ["true", "1", "y", "yes"]:
                res = True
            else:
                res = False
        elif j.data.types.int.check(default):
            res = int(val)
        elif j.data.types.float.check(default):
            res = int(val)
        else:
            res = str(val)
        return res
