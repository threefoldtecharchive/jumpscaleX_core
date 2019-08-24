# base classes for JumpscaleX

## the lowest base class:

- [j.baseclasses.object](jsbase.md)
- [j.application.JSBaseDataObjClass]()          #like JSBase but add management JSXObj to the class

Each class needs to inherrit of one of those, with JSX data object use the JSBaseDataObjClass otherwise JSBaseClass

## how to be factory

- JSBaseFactory                                 #use for when at j... factory level, is when you need e.g. test features

use this when you create children

## the more advances ones:

- [j.application.JSFactoryBaseClass](factorybaseclass.md)
- [j.baseclasses.object_config](config.md)
- [j.baseclasses.objects_config_bcdb](configs.md)


## properties available on all base classes


- _location  : e.g. j.clients.ssh, is always the location name of the highest parent
- _name : name of the class itself in lowercase
- _key: is a unique key per object based on _location,_name and if relevant "name" of model inside, is used in the logger

### logging on a jumpscale object

- _logger_enable() will make sure self._logger_min_level = 0 (is for all classes related to self._location
- _logger_minlevel_set(100), 100 means no logging, 0 is all logging
  - 10 means logs debugs and up
  - 15 means logs stdout & above, ...
  - will configure child & parent classes as well as object (in same jumpscale location)

- _log_debug : method to log a debug statement
- _print : print to stdout but also log
- _log_info : method to log a info statement
- _log_warning : method to log a warning statement
- _log_error : method to log an error statement
- _log_critical : method to log a critical statement


### how do baseclasses call each other

- the top class (who inherits from someone else)
    - is called with topclass=True in initator
- self.__init__() is called for each childclass, the most base class called first
- self._init() is called from the topclass only, meant to be implemented on topclass
- self._init2() is called from the topclass only, implemented on baseclasses, will call all child classes
    - the most base class is called last


### create your own classes

if you create your own classes who inherit from JSBase (which should be all)
use following patern

```python

class MyClass(JSBase):

    def _init(self):

        #your own initialization parts

```

do not implement your own __init__() !!!


