## JS Base Class

This is the baseclass used by all other base classes, its the lowest level one.
Implements

- logging
- 

```
class JSBase:
    def __init__(self, parent=None, topclass=True, **kwargs):
        """
        :param parent: parent is object calling us
        :param topclass: if True means no-one inherits from us
        """
        self._parent = parent
        self._class_init()  # is needed to init class properties

        ...

        self._obj_cache_reset()
```

It contains all the logic that handles the `__jslocation__` property that attaches the class somewhere in the Jumpscale namespace. It also contais logic to control the [logger](readme.md#logging-on-a-jumpscale-object) and to inspect properties and methods on the parent class.

### class properties

used to let e.g. our shell work properly

- self.__class__._methods_ = []  
- self.__class__._properties_ = []
- self.__class__._inspected_ = False

### how does it initialize

- definition of types of developers
    - core developer : someone who workds on the core of jumpscale e.g. the core baseclasses themselves or how logging works (mainly despiegk today)
    - jsx developer  : someone who develops in jumpscale, can create base classes for end developers, but is not core developer
    - end developer  : scripter who uses JSX to do his business with, will inherit from baseclasses as created by jsx developer or core developer

the initialization mechanism

- __init__ only done on JSBASE lowest level

```python
self._init_class(topclass=topclass)  # is needed to init class properties

self._init_pre(**kwargs)
self._init(**kwargs)
self._init_post(**kwargs)

self._obj_cache_reset()
```

#### class level

- _class_init
  - as used by jsx developer
  - will make sure that all classes are configured properly e.g. logging

#### obj level

- _init_pre(**kwargs) : used by core or jsx developer (NOT BY end developer)
- _init((*kwargs))    : used by developer of the class which inherits from JSBase, the class as used by end developer (should not use __init__)
- _init_post(**kwargs): to be used by end developer only, has **kwargs inside which was pased in by constructor

#### top class idea

when calling the _init_class we need to make sure this is only done in the class as will be used by an end developer.
Otherwise we call the class on a too low level.

- the top class (who inherits from someone else)
    - is called with topclass=True in initator

#### parent * children idea

- self._parent = parent  : if we are a child, this allows us to go back to the parent
- self.__children = []    : a list of our children  can be dynamically fetched using : self.__children_get()

allows us to create hyrarchies of objects

### obj properties

- _objid  : is handy in generic way how to find a unique object id will try different mechanism's to come to a useful id
- _cache  : caching mechanism
- _ddict  : a dict of the properties (not starting with _)

### obj properties internal usage e.g. for kosmos shell

filter is 
```
:param filter: is '' then will show all, if None will ignore _
        when * at end it will be considered a prefix
        when * at start it will be considered a end of line filter (endswith)
        when R as first char its considered to be a regex
        everything else is a full match
```


```python
def __parent_name_get()

#e.g. VMFactory has VM's as children, when used by means of a DB then they are members
def __children_names_get(self, filter=None)
def __children_get(self, filter=None): # if nothing then is self.__children
def __child_get(self, name=None, id=None) # finds a child based on name or id

#member comes out of a DB e.g. BCDB e.g. all SSH clients which are configured with data out of BCDB
def __members_names_get_(self, filter=None)
def __members_get(self, filter=None) #normally coming from a database e.g. BCD e.g. disks in a server, or clients in SSHClientFactory
def __member_get(self, name=None, id=None)

def __dataprops_names_get(self, filter=""):   #get properties of the underlying data model e.g. JSXOBJ
def __dataprops_get(
def __dataprop_get(

def __methods_names_get(self, filter=""): # return the names of the methods which were defined at __init__ level by the developer
def __properties_names_get(self, filter=""): #return the names of the properties which were defined at __init__ level by the developer

def __check(self)  #only use for debugging purposes, if you're not sure an object is well used can use this to check

```


#### some important props

- self.__class__.__protected = True  is True will make sure only known props at start can be set

### obj methods

```python
 def _print(self, msg, cat=""):
        self._log(msg, cat=cat, level=15)

def _log_debug(self, msg, cat="", data=None, context=None, _levelup=1):
    self._log(msg, cat=cat, level=10, data=data, context=context, _levelup=_levelup)

def _log_info(self, msg, cat="", data=None, context=None, _levelup=1):
    self._log(msg, cat=cat, level=20, data=data, context=context, _levelup=_levelup)

def _log_warning(self, msg, cat="", data=None, context=None, _levelup=1):
    self._log(msg, cat=cat, level=30, data=data, context=context, _levelup=_levelup)

def _log_error(self, msg, cat="", data=None, context=None, _levelup=1):
    self._log(msg, cat=cat, level=40, data=data, context=context, _levelup=_levelup)

def _log_critical(self, msg, cat="", data=None, context=None, _levelup=1):
    self._log(msg, cat=cat, level=50, data=data, context=context, _levelup=_levelup)

def _log(self, msg, cat="", level=10, data=None, context=None, _levelup=1):
    """

    :param msg: what you want to log
    :param cat: any dot notation category
    :param level: level of the log
    :return:

    can use {RED}, {RESET}, ... see color codes

        levels:

        - CRITICAL 	50
        - ERROR 	40
        - WARNING 	30
        - INFO 	    20
        - STDOUT 	15
        - DEBUG 	10

def _done_check(self, name="", reset=False):
def _done_set(self, name="", value="1"):
def _done_get(self, name=""):
def _done_reset(self, name=""):
    """
    if name =="" then will remove all from this object
    :param name:
    :return:
    """

def _test_run(self, name="", obj_key="main", die=True, **kwargs):
    """

    :param name: name of file to execute can be e.g. 10_test_my.py or 10_test_my or subtests/test1.py
                the tests are found in subdir tests of this file

            if empty then will use all files sorted in tests subdir, but will not go in subdirs

    :param obj_key: is the name of the function we will look for to execute, cannot have arguments
            to pass arguments to the example script, use the templating feature, std = main


    :return: result of the tests


```

### safety mechanisms

- properties which are not known at __init__ time can not be set later