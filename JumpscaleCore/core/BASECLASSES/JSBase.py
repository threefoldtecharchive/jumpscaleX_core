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
import os

# import copy
# import sys
import inspect
import types
from .JSDict import JSDict


class JSBase:

    __init_class_done = False
    _protected = False
    _dirpath_ = ""
    # _objcat_name = ""
    _cache_expiration = 3600
    _test_runs = {}
    _test_runs_error = {}
    _classname = ""
    _location = ""
    _logger_min_level = 10
    _logger_enabled = True
    _class_children = []

    def __init__(self, parent=None, **kwargs):
        """
        :param parent: parent is object calling us
        :param topclass: if True means no-one inherits from us
        """

        self._protected = False
        self._parent = parent
        self._children = JSDict()
        self._properties_ = None
        self._methods_ = None
        if "parent" in kwargs:
            kwargs.pop("parent")
        self._init_pre(**kwargs)
        self._init_pre2(**kwargs)
        self.__init_class()
        self._obj_cache_reset()
        self._init(**kwargs)
        self._init_factory(**kwargs)
        self._init_post(**kwargs)
        self._init_post_attr()

    def _children_reset(self):
        self._children = JSDict()

    @property
    def _properties(self):
        if self._properties_ == None:  # need to be specific None
            self._inspect()
        return self._properties_

    @property
    def _methods(self):
        if self._methods_ == None:
            self._inspect()
        return self._methods_

    def _hasattr(self, key):
        """
        will only returh the properties, methods & children (will not lookin jsconfig data)
        :param name:
        :return:
        """
        if key in self._properties:
            return True
        if key in self._methods:
            return True
        if key in self._children:
            return True
        return False

    def __init_class(self):

        if not self.__class__.__init_class_done:

            # short location name:

            if not self.__class__._classname:
                self.__class__._classname = j.core.text.strip_to_ascii_dense(str(self.__class__)).split(".")[-1].lower()
                # name = str(self.__class__).split(".")[-1].split("'", 1)[0].lower()  # wonder if there is no better way

            if "__jslocation__" in self.__dict__:
                self.__class__._location = self.__jslocation__
            elif "__jslocation__" in self.__class__.__dict__:
                self.__class__._location = self.__class__.__jslocation__
            elif "__jscorelocation__" in self.__dict__:
                self.__class__._location = self.__jslocation__
            else:
                self.__class__._location = None
                parent = self._parent
                while parent is not None:
                    if "__jslocation__" in parent.__dict__:
                        # if self._hasattr(parent, "__jslocation__"):
                        self.__class__._location = parent.__jslocation__
                        break
                    parent = parent._parent
                if self.__class__._location is None:
                    self.__class__._location = self.__class__._classname

            # # walk to all parents, let them know that there are child classes
            # self.__class__._class_children = []
            # parent = self._parent
            # while parent is not None:
            #     if parent.__class__ not in parent._class_children:
            #         parent._class_children.append(parent.__class__)
            #     parent = parent._parent

            # if self.__class__._location.lower() != self.__class__._classname.lower():
            #     self.__class__._key = "%s:%s" % (self.__class__._location, self.__class__._classname)
            # else:
            #     self.__class__._key = self.__class__._classname.lower()

            self.__init_class_post()

            self.__class__.__init_class_done = True

            self._log_debug("***CLASS INIT 1: %s" % self.__class__._classname)

            # lets make sure the initial loglevel gets set
            self._logger_set(children=False, parents=False)

    def __init_class_post(self):
        pass

    def _inspect(self, include_prefix=None, exclude_prefix=None):
        """

        returns properties and methods of the class/object

        properties,methods = self._inspect()

        :return: (properties,methods)
        """
        # self._log("INSPECT:%s" % self.__class__)
        properties = []
        methods = []
        for name, obj in inspect.getmembers(self.__class__):
            if include_prefix and not name.startswith(include_prefix):
                continue
            if exclude_prefix and name.startswith(exclude_prefix):
                continue
            if inspect.ismethod(obj):
                methods.append(name)
            elif inspect.ismethoddescriptor(obj):
                continue
            elif inspect.isfunction(obj):
                methods.append(name)
            elif inspect.isclass(obj):
                properties.append(name)
            elif inspect.isgetsetdescriptor(obj):
                continue
            else:
                properties.append(name)

        for item in self.__dict__.keys():
            if include_prefix and not name.startswith(include_prefix):
                continue
            if exclude_prefix and name.startswith(exclude_prefix):
                continue
            if item not in properties:
                properties.append(item)

        self._properties_ = properties
        self._methods_ = methods

        return self._properties_, self._methods_

    @property
    def _key(self):
        return self._classname

    @property
    def _name(self):
        return self._key

    def _init(self, **kwargs):
        pass

    def _init_pre(self, **kwargs):
        """
        meant to be used by developers of the base classes
        :return:
        """
        pass

    def _init_pre2(self, **kwargs):
        """
        meant to be used by developers of the base classes
        :return:
        """
        pass

    def _init_factory(self, **kwargs):
        """
        only used by factory class
        :return:
        """
        pass

    def _init_post(self, **kwargs):
        """
        meant to be used by developers of the base classes
        :return:
        """
        pass

    def _init_post_attr(self, **kwargs):
        """
        only there for the attr baseclass
        :return:
        """
        pass

    def _obj_cache_reset(self):
        """
        this empties the runtime state of an obj and the logger and the testruns
        :return:
        """

        self.__class__._test_runs = {}
        self._cache_ = None
        self._objid_ = None

        for key, obj in self._children.items():
            obj._obj_cache_reset()

    def _obj_reset(self):
        """
        to remove property underlying values, good for mem reclaim or sub process management
        :return:
        """
        pass

    @property
    def _dirpath(self):
        if self.__class__._dirpath_ == "":
            self.__class__._dirpath_ = os.path.dirname(inspect.getfile(self.__class__))

            if not self.__class__._dirpath_:
                self.__class__._dirpath_ = j.sal.fs.getcwd()

        return self.__class__._dirpath_

    @property
    def _objid(self):
        if self._objid_ is None:
            id = self.__class__._location
            id2 = ""
            if "_data" in self.__dict__:
                try:
                    id2 = self._data.name
                except:
                    pass
                if id2 == "":
                    try:
                        if self._data.id is not None:
                            id2 = self._data.id
                    except:
                        pass
            if id2 == "":
                for item in ["instance", "_instance", "_id", "id", "name", "_name"]:
                    if item in self.__dict__ and self.__dict__[item]:
                        self._log_debug("found extra for obj_id")
                        id2 = str(self.__dict__[item])
                        break
            if id2 != "":
                self._objid_ = "%s_%s" % (id, id2)
            else:
                self._objid_ = id
        return self._objid_

    def _logger_enable(self):
        self._logger_set(0)

    @property
    def _cache(self):
        if self._cache_ is None:
            self._cache_ = j.core.cache.get(self._objid, expiration=self._cache_expiration)
        return self._cache_

    @property
    def _ddict(self):
        res = JSDict()
        for key in self.__dict__.keys():
            if not key.startswith("_"):
                v = self.__dict__[key]
                if not isinstance(v, types.MethodType):
                    res[key] = v
        return res

    def __check(self):
        for key in self.__dict__.keys():
            if key not in self.__class__._names_properties_:
                raise j.exceptions.Base("a property was inserted which should not be there")

    ########################## LOGGING ##########################

    def _logging_enable_check(self):
        """

        check if logging should be disabled for current js location

        according to logger includes and excludes (configured)
        includes have a higher priority over excludes

        will not take minlevel into consideration, its only the excludes & includes

        :return: True if logging is enabled
        :rtype: bool
        """
        if j.core.myenv.config.get("DEBUG", False):
            return True

        def check(checkitems):
            key = ""
            location = ""
            try:
                key = self._key
            except:
                key = self._classname
            if self._hasattr("_location"):
                try:
                    location = self._location
                except:
                    pass
            for finditem in checkitems:
                finditem = finditem.strip().lower()
                if finditem == "*":
                    return True
                if finditem == "":
                    continue
                if "*" in finditem:
                    if finditem[-1] == "*":
                        # means at end
                        if key.startswith(finditem[:-1]):
                            return True
                    elif finditem[0] == "*":
                        if key.endswith(finditem[1:]):
                            return True
                    else:
                        raise j.exceptions.Base("find item can only have * at start or at end")
                else:
                    if location in [finditem, f"j.{finditem}"]:
                        return True
            return False

        if check(j.core.myenv.log_includes) and not check(j.core.myenv.log_excludes):
            return True
        return False

    def _logger_set(self, minlevel=None, children=True, parents=True):
        """

        :param min_level if not set then will use the LOGGER_LEVEL from /sandbox/cfg/jumpscale_config.toml

        make sure that logging above minlevel will happen, std = 100
        if 100 means will not log anything


        - CRITICAL 	50
        - ERROR 	40
        - WARNING 	30
        - INFO 	    20
        - STDOUT 	15
        - DEBUG 	10
        - NOTSET 	0


        if parents and children: will be set on all classes of the self.location e.g. j.clients.ssh (children, ...)

        if minlevel specified then it will always consider the logging to be enabled

        :return:
        """
        if not self._logging_enable_check():
            self.__class__._logger_enabled = False
            return
        if minlevel is None:
            minlevel = int(j.core.myenv.config.get("LOGGER_LEVEL", 15))

        self.__class__._logger_min_level = minlevel

        if parents:
            parent = self._parent
            while parent is not None:
                parent._logger_set(minlevel=minlevel)
                parent = parent._parent

        if children:
            for kl in self.__class__._class_children:
                # print("%s:minlevel:%s"%(kl,minlevel))
                kl._logger_min_level = minlevel

    def _print(self, msg, cat=""):
        self._log(msg, cat=cat, level=15)

    def _log_debug(self, msg, cat="", data=None, context=None, _levelup=1, exception=None):
        self._log(msg, cat=cat, level=10, data=data, context=context, _levelup=_levelup, exception=exception)

    def _log_info(self, msg, cat="", data=None, context=None, _levelup=1, exception=None):
        self._log(msg, cat=cat, level=20, data=data, context=context, _levelup=_levelup, exception=exception)

    def _log_warning(self, msg, cat="", data=None, context=None, _levelup=1, exception=None):
        self._log(msg, cat=cat, level=30, data=data, context=context, _levelup=_levelup, exception=exception)

    def _log_error(self, msg, cat="", data=None, context=None, _levelup=1, exception=None):
        self._log(msg, cat=cat, level=40, data=data, context=context, _levelup=_levelup, exception=exception)

    def _log_critical(self, msg, cat="", data=None, context=None, _levelup=1, exception=None):
        self._log(msg, cat=cat, level=50, data=data, context=context, _levelup=_levelup, exception=exception)

    def _log(
        self,
        msg,
        cat="",
        level=10,
        data=None,
        context=None,
        _levelup=0,
        stdout=True,
        tb=None,
        data_show=True,
        exception=None,  # is jumpscale/python exception
        replace=True,  # to replace the color variables for stdout
    ):
        """

        :param msg: what you want to log
        :param cat: any dot notation category
        :param context: e.g. rack aaa in datacenter, method name in class, ...

        can use {RED}, {RESET}, ... see color codes
        :param level:
            - CRITICAL 	50
            - ERROR 	40
            - WARNING 	30
            - INFO 	    20
            - STDOUT 	15
            - DEBUG 	10


        :param _levelup 0, if e.g. 1 means will go 1 level more back in finding line nr where log comes from
        :param stdout: return as logdict or send to stdout
        :param: replace to replace the color variables for stdout
        :param: exception is jumpscale/python exception

        """

        if j.application.debug or (self._logger_enabled and self._logger_min_level - 1 < level):
            # now we will log

            frame_ = inspect.currentframe().f_back
            if _levelup > 0:
                levelup = 0
                while frame_ and levelup < _levelup:
                    frame_ = frame_.f_back
                    levelup += 1

            if not context:
                try:
                    context = self._key
                except Exception as e:
                    context = "UNKNOWN"
                    pass  # TODO:*1 is not good

            return j.core.tools.log(
                msg=msg,
                cat=cat,
                level=level,
                data=data,
                context=context,
                tb=tb,
                data_show=data_show,
                exception=exception,  # is jumpscale/python exception
                replace=replace,  # to replace the color variables for stdout
                stdout=stdout,  # return as logdict or send to stdout
                frame_=frame_,
            )

    #################### DONE ##############################

    def _done_key(self, name):
        if name == "":
            key = self._objid
        else:
            key = "%s:%s" % (self._objid, name)
        return key

    def _done_check(self, name="", reset=False):
        if reset:
            self._done_delete(name=name)
        return j.core.myenv.state_get(self._done_key(name))
        # return j.core.db.hexists("done", key)

    def _done_set(self, name=""):
        j.core.myenv.state_set(self._done_key(name))
        # return j.core.db.hset("done", self._done_key(name), value)

    def _done_delete(self, name=""):
        j.core.myenv.state_delete(self._done_key(name))
        # return j.core.db.hset("done", self._done_key(name), value)

    def _done_reset(self):
        """
        if name =="" then will remove all from this object
        :param name:
        :return:
        """
        name = self._done_key("")
        j.core.myenv.states_delete(name)
        # if name == "":
        #     for item in j.core.db.hkeys("done"):
        #         item = item.decode()
        #         # print("reset todo:%s" % item)
        #         if item.find(self._objid) != -1:
        #             j.core.db.hdel("done", item)
        #             # print("reset did:%s" % item)
        # else:
        #     return j.core.db.hdel("done", "%s:%s" % (self._objid, name))

    ################### mechanisms for autocompletion in kosmos

    def __name_get(self, item):
        """
        helper mechanism to come to name
        """
        if isinstance(item, str) or isinstance(item, int):
            name = str(item)
            return name
        elif isinstance(item, j.baseclasses.object_config):
            return item.name
        elif isinstance(item, j.baseclasses.object):
            return item._name
        else:
            raise j.exceptions.JSBUG("don't know how to find name")

    def _filter(self, filter=None, llist=[], nameonly=True, unique=True, sort=True):
        """

        :param filter: is '' then will show all, if None will ignore _
                when * at end it will be considered a prefix
                when * at start it will be considered a end of line filter (endswith)
                when R as first char its considered to be a regex
                everything else is a full match
        :param llist:
        :param nameonly: will not return the items of the list but names derived from the list members
        :param unique: will make sure there are no duplicates
        :param sort: sort but only when nameonly
        :return:
        """
        res = []
        for item in llist:
            name = self.__name_get(item)
            # self._log_debug("filtername:%s" % name)
            if not name:
                continue
            if name.startswith("_JSBase"):
                continue
            if filter:
                if not filter.startswith("_") and name.startswith("_"):
                    continue
                if filter.startswith("_") and not filter.startswith("__") and name.startswith("__"):
                    # remove __ if we only ask for _
                    continue
                if filter.endswith("*"):
                    filter2 = filter[:-1]
                    if not name.startswith(filter2):
                        continue
                elif filter.startswith("*"):
                    filter2 = filter[1:]
                    if not name.endswith(filter2):
                        continue
                elif filter.startswith("R"):
                    j.shell()
                    filter3 = filter[1:]
                    w
                else:
                    if not name == filter:
                        continue
            else:
                if name.startswith("_"):
                    continue

            if nameonly:
                item = name
            if unique:
                if item not in res:
                    res.append(item)
            else:
                res.append(item)

        if nameonly and sort:
            res.sort()

        return res

    def _parent_name_get(self):
        if self._parent:
            return self.__name_get(self._parent)
        return ""

    def _mother_id_get(self):
        """
        this goes to all parents till it finds a parent which has a model attached
        this is to find the parent which acts as the mother for the children
        when you do a search only the children of this mother will be shown
        :return:
        """
        obj = self
        while obj and obj._parent:
            if isinstance(obj._parent, j.baseclasses.object_config):
                if obj._parent._id is None:
                    if obj._parent.name is None:
                        raise j.exceptions.JSBUG("cannot happen, there needs to be a name")
                    else:
                        obj._parent.save()
                        assert obj._parent._id > 0
                        return obj._parent._id
                else:
                    return obj._parent._id
            obj = obj._parent
        # means we did not find a parent which can act as mother
        return None

    def _children_names_get(self, filter=None):
        return self._filter(filter=filter, llist=self._children_get(filter=filter))

    def _children_get(self, filter=None):
        """
        if nothing then is self._children

        :param filter: is '' then will show all, if None will ignore _
                when * at end it will be considered a prefix
                when * at start it will be considered a end of line filter (endswith)
                when R as first char its considered to be a regex
                everything else is a full match

        :return:
        """
        if self._hasattr("_children"):
            children = self._children.values()
            return self._filter(filter=filter, llist=children, nameonly=False)
        else:
            return []

    def _children_delete(self, recursive=True, filter=None):
        """
        filter only applies on the first children search
        :param recursive:
        :param filter:
        :return:
        """
        for child in self._children_get(filter=filter):
            if child._hasattr("delete"):
                child.delete(recursive=recursive)
            else:
                child._children_delete(recursive=recursive)

    def _child_get(self, name=None, id=None):
        """
        finds a child based on name or id
        :param name:
        :param id:
        :return:
        """
        for item in self._children_get():
            if name:
                assert isinstance(name, str)
                if self.__name_get(item) == name:
                    return item
            elif id:
                id = int(id)
                if item.id == id:
                    return item
            else:
                raise j.exceptions.Base("need to specify name or id")
        return None

    def _dataprops_names_get(self, filter=None):
        """
        e.g. in a JSConfig object would be the names of properties of the jsxobject = data
        e.g. in a JSXObject would be the names of the properties of the data itself

        :return: list of the names
        """
        return []

    def _methods_names_get(self, filter=None):
        """
        return the names of the methods which were defined at __init__ level by the developer

        :param filter: is '' then will show all, if None will ignore _
                when * at end it will be considered a prefix
                when * at start it will be considered a end of line filter (endswith)
                when R as first char its considered to be a regex
                everything else is a full match

        """
        return self._filter(filter=filter, llist=self._methods)

    def _properties_names_get(self, filter=None):
        """
        return the names of the properties which were defined at __init__ level by the developer

        :param filter: is '' then will show all, if None will ignore _
                when * at end it will be considered a prefix
                when * at start it will be considered a end of line filter (endswith)
                when R as first char its considered to be a regex
                everything else is a full match

        """
        others = self._children_names_get(filter=filter)
        if self._hasattr("_parent"):
            pname = self._parent_name_get()  # why do we need the parent name?
            if pname not in others:
                others.append(pname)
        res = [i for i in self._filter(filter=filter, llist=self._properties) if i not in others]
        return res

    def _properties_methods_names_get(self):
        return self._properties + self._methods

    def _props_all_names(self):
        l = (
            self._children_names_get()
            + self._properties_names_get()
            + self._dataprops_names_get()
            + self._methods_names_get()
        )
        return l

    def _prop_exist(self, name):
        """
        :param name:
        :return:
        """
        raise

    def _children_recursive_get(self):
        res = []
        for child in self._children.values():
            res.append(child)
            res += child._children_recursive_get()
        return res

    ###################

    def __repr__(self):

        out = "{YELLOW}## %s{BLUE} %s{RESET}\n\n" % (
            # self._objcat_name,
            self.__class__._location,
            self.__class__.__name__,
        )

        def add(name, color, items, out):
            # self._log_debug(items)
            if len(items) > 0:
                out += "{%s}### %s:\n" % (color, name)
                if len(items) < 20:
                    for item in items:
                        self._log_debug(item)
                        item = item.rstrip()
                        if name in ["data", "properties"]:
                            try:
                                v = j.core._data_serializer_safe(getattr(self, item)).rstrip()
                                if "\n" in v:
                                    # v = j.core.tools.text_indent(content=v, nspaces=4)
                                    v = "\n".join(v.split("\n")[:1])
                                    out += " - %-20s : {GRAY}%s{%s}\n" % (item, v, color)
                                else:
                                    out += " - %-20s : {GRAY}%s{%s}\n" % (item, v, color)

                            except Exception as e:
                                out += " - %-20s : {GRAY}ERROR ATTRIBUTE{%s}\n" % (item, color)
                        else:
                            out += " - %s\n" % item
                else:
                    out += " - ...\n"
            out += "\n"
            return out

        out = add("children", "GREEN", self._children_names_get(), out)
        out = add("properties", "YELLOW", self._properties_names_get(), out)
        out = add("data", "BLUE", self._dataprops_names_get(), out)

        out += "{RESET}"

        out = j.core.tools.text_replace(out, die_if_args_left=False)
        print(out)

        # TODO: *1 dirty hack, the ansi codes are not printed, need to check why
        return ""

    def __str__(self):
        """
        this will give us cleaner reporting in logs, the repr needs to be big, is for user
        __str__ is for logging, printing, ...
        :return:
        """
        return "jsxobj:%s:%s" % (self.__class__._location, self.__class__.__name__)
