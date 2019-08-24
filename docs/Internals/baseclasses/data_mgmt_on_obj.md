# data management on a class

## principles

Change the properties directly on the object

e.g.

```python
mysshclient = j.clients.ssh.a
mysshclient.addr = ...

```


## data_update method

- can be used to update data from dict or **kwargs.
- Will update the underlying object.
- Will not save.
- Will call trigger self._data_update()


## triggers

Triggers are defined on model level.

```def Trigger_add(self, method):```

will call the method as follows before doing a set in DB

- method(model=model,obj=obj,kosmosinstance=None, action=None, propertyname=None)
- kosmosinstance only if _model used in an jumpscale configuration enabled class
- action is in "new, change, get,set_pre,set_post,delete"  done on DB layer
- propertyname only relevant for changes, is when object property gets changed e.g. ipaddr...

to add a custom Trigger on kosmos obj do

```
def mymethod(self,model,obj,kosmosinstance=None, action=None, propertyname=None):
    #do something e.g. manipulate the data model before storing in DB

kosmosobj._model.trigger_add(mymethod)
```


### example how to use

```python

class SomeClass(...):

    def _init(self,**kwargs):

        self._model.trigger_add(self._data_update_color)

    @staticmethod
    def _data_update_color(model,obj,kosmosinstance=None, action=None, propertyname=None):
        self = kosmosinstance  #this way code is same and can manipulate self like in other methods
        if propertyname=="color":
            j.shell()


o = SomeClass()
o.color = "red"
#this will now triger the _data_update_color method & because propertyname matches it will get in shell

easiest to add as staticmethod, that way its part of the class


```






