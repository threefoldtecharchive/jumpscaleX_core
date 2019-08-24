# JSXObject

is result of using a [JSXSchema] .

has no notion of config management, its just the data object by itself.

```python
#how to get 
j.data.schema...  

def new(self, capnpdata=None, serializeddata=None, datadict=None, bcdb=None):
    """
    new schema_object using data and capnpbin

    :param serializeddata is data as serialized by j.serializers.jsxobject (has prio)  : #TODO: check
    :param capnpdata is data in capnpdata
    :param datadict is dict of arguments, only dict supported

    :param model: will make sure we save in the model
    :return:
    """
```

sa
