# JS Base Class

This is the baseclass used by all other base classes, its the lowest level one.
Implements

- initialization see [Initialization](Initialization.md)
- logging
- logic that handles the `__jslocation__` property that attaches the class somewhere in the Jumpscale namespace. 
- logic to control the [logger](readme.md#logging-on-a-jumpscale-object) and to inspect properties and methods on the parent class.

### class properties

- ```self.__class__._classname``` is ascii dense name
- ```self.__class__.__jslocation__``` is the unique location in our j... tree
- ```self.__class__._location``` gets resolved to a unique class name to identify the class
    - if ```__jslocation__``` exists will use that
    - if NOT ```__jslocation__``` then will be ```_classname```
- ```self.__class__._methods_``` = []  
- ```self.__class__._properties_``` = []
- ```self.__class__._inspected_``` = False        : once inspection done then _methods & _properties filled in


#### parent * children idea

- self._parent = parent  : if we are a child, this allows us to go back to the parent
- self.__children = []    : a list of our children  can be dynamically fetched using ```self.__children_get()```

allows us to create hyrarchies of objects

### some obj properties

- _objid  : is handy in generic way how to find a unique object id will try different mechanism's to come to a useful id
    - used by e.g caching mechanism of jsbase
    - it serves as unique identification of a jsbase object and takes into consideration name, id, ...

- _cache  : caching mechanism
- _ddict  : a dict of the properties (not starting with _)

### filter for methods/property resolution in shell

filter is 
```
:param filter: is '' then will show all, if None will ignore _
    when * at end it will be considered a prefix
    when * at start it will be considered a end of line filter (endswith)
    when R as first char its considered to be a regex
    everything else is a full match
```


## Methods:

### Initialization of the class level

- walk to all parents, let them know that there are child classes, each child class has `__jslocation__` variable which defines it's location as a short path
- __jslocation__ example: `j.builders.db.zdb.build()`
    - To execute this command db builders's dir has a factory class which has location variable `__jslocation__ = "j.builders.db"` also to point to all child classes. same goes with clients, servers, ..etc
    - This is done in `__init_class` method</p>

### Logging Methods

All jumpscale logging methods and logic are implemented in JSBase.
Logs have levels you can pass it as a parameter through `_logger_set()` method param min_level if not set then will use the LOGGER_LEVEL from `sandbox/cfg/jumpscale_config.toml`,

- `log()`: method takes whatever you want to log, also has a parameter log-level
- `_logging_enable_check`:  check if logging should be disabled for current js location
- `_logger_enable()`: will make sure self._logger_min_level = 0 (is for all classes related to self._location. 
- `_log_debug` : method to log a debug statement. 
- `_print` : print to stdout but also log. 
- `_log_info` : method to log a info statement. 
- `_log_warning` : method to log a warning statement. 
- `_log_error` : method to log an error statement. 
- `_log_critical` : method to log a critical statement. 
</p>

### Logic for mainly auto completion in shell

- To make autocompeletion in kosmos shell, we need to know the children of each class and the methods or properties in it also the data if it contains, we will walk through the methods that do so.
- `_name`: is a property, resolves to the name of the object
- `_filter`: 
    - Check names to view only required once which means it won't show names starts with "_" or "__" unless you type it. 
    - It uses other methods as helpers like `_parent_name_get`, `_child_get` ..



```python
def __parent_name_get():
#resolve name of parent if any parent, otherwise None
def __children_names_get(self, filter=None):
#e.g. VMFactory has VM's as children, when used by means of a DB then they are members
def __children_get(self, filter=None): 
# if nothing then is self.__children
def __child_get(self, name=None, id=None): 
# finds a child based on name or id

def __members_names_get_(self, filter=None)
#member comes out of a DB e.g. BCDB e.g. all SSH clients which are configured with data out of BCDB
def __members_get(self, filter=None): #normally coming from a database e.g. BCD e.g. disks in a server, or clients in SSHClientFactory
def __member_get(self, name=None, id=None):

def __dataprops_names_get(self, filter=""):
#get properties of the underlying data model e.g. JSXOBJ
def __dataprops_get():
def __dataprop_get():

def __methods_names_get(self, filter=""):
# return the names of the methods which were defined at __init__ level by the developer
def __properties_names_get(self, filter=""):
#return the names of the properties which were defined at __init__ level by the developer

```

### State on execution of methods (the _done methods)

- Is a flag to save the state of execting methods.
- `_done_set`
    - saves that this method had been executed so, it won't run again unless you change the state
- `_done_delete`, `_done_reset`,`_done_check`, `_done_key`
