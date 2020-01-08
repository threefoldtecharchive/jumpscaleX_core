## Triggers

Triggers are defined on model level.

```def Trigger_add(self, method):```

will call the method as follows before doing a set in DB

- method(model=model,obj=obj,kosmosinstance=None, action=None, propertyname=None)
- kosmosinstance only if _model used in an jumpscale configuration enabled class
- action is in "new, change, get,set_pre,set_post,delete"  done on DB layer
- propertyname only relevant for changes, is when object property gets changed e.g. ipaddr...
- return None or the changed object

to add a custom Trigger on kosmos obj do

```python
def mymethod(self,model,obj,kosmosinstance=None, action=None, propertyname=None):
    #do something e.g. manipulate the data model before storing in DB

kosmosobj._model.trigger_add(mymethod)
```

### trigger example:

```python
def _data_update_color(model,obj,kosmosinstance=None, action=None, propertyname=None):
    return obj,True

```

the creator of trigger can return

-  obj,stop
-  None
-  obj

stop can be True or False

if stop then next triggers will not be called and the data will not be saved (if that would be relevant)

### example how to use

```python

class SomeClass(...):

    def _init(self,**kwargs):
        self._model.trigger_add(self._data_update_color)

    @staticmethod
    def _data_update_color(model,obj, action=None, propertyname=None):
        if propertyname=="color":
            j.shell()
        stop=False
        return obj,stop


o = SomeClass()
o.color = "red"
#this will now triger the _data_update_color method & because propertyname matches it will get in shell

easiest to add as staticmethod, that way its part of the class


```

## pre-defined triggers

### obj is retrieved from a model

- action = get
- obj = obj which is retrieved
- property = None

obj can be modified by the trigger and will be returned that way from model.get()

### when property changes on a JSX data object

- calls: action="change" & propertyname is filled in

### obj gets deleted

- calls: action="delete"

### obj gets saved

from model or directly from jsxobj

- calls: action="set_pre" before the data gets saved
- if stop is True then the save or delete will not happen (data modification)
- calls: action="set_post" after data is saved

### a new object gets created

- calls: action="new"

obj can be manipulated in the trigger, the manipulated one will be returned

### schema gets changed

- action = schema_change
- obj = None or if obj is filled in (so can be both)
- property = None

### model gets unloaded out of mem

- action = stop
- obj = None or if obj is filled in (so can be both)
- property = None

allows us to e.g. save the data, this gets called when e.g. threebotserver stops
