
```python
#constructor
def new self, capnpdata=None, serializeddata=None, datadict=None, model=None)
    """
    new schema_object using data and capnpbin

    :param serializeddata is data as serialized by j.serializers.jsxobject (has prio)  : #TODO: check
    :param capnpdata is data in capnpdata
    :param datadict is dict of arguments, only dict supported

    :param model: will make sure we save in the model
    :return:
    """
```

the result of a using the schema is a ```JSXObject``` = a Jumpscale Data Object  (JSX = Jumpscale X)

