# How does each JSX Object initialize


```python
def __init__(self, parent=None,**kwargs):
"""
:param parent: parent is object calling us
"""
# if set, cannot fill in properties which are not set before _init_jsconfig_post()
self._protected = False
# the parent of this object
self._parent = parent
if "parent" in kwargs:
    kwargs.pop("parent")
# the children of this object
self._children = JSDict()

# the properties known to this object, others will be protected
# resolved by _inspect(), are made lazy loading, if you want to use use self._properties
self._properties_ = None
# the methods known to this object
self._methods_ = None

# meant to be used by developers of the base classes, is the initial setting of properties
self._init_pre(**kwargs)

# init custom done for jsconfig & jsconfigs objects (for config mgmt)
self._init_jsconfig(**kwargs)

# only relevant for actors in 3bot actors, used to initialize the actor
self._init_actor(**kwargs)

# find the class related properties
# will afterwards call self.__init_class_post()
self.__init_class()

# resets the caches
self._obj_cache_reset()

# the main init function for an object
# this is the main one to be used by JSX end developer, and the only method to be filled in
self._init(**kwargs)

# only used by factory class
# a factory class can produce jsconfig or jsconfigs objects (are part of children)
self._init_factory(**kwargs)

# allow the jsconfig class to do the post initialization
# here we check to save an object to the database if that would be required
# objects will not be saved untill here, so in the _init we can manipulate the data
self._init_jsconfig_post(**kwargs)

# this is only used when the class inherits from Attr() class
# will also do an inspect to make sure we have protected the attributes, only relevant when Attr based class
        self._init_attr()
```

this logic is in jsbase class and is used by every class.

