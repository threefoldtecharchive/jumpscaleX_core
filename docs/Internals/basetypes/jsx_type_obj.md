# jumpscale X type object

These are objects which we implement ourselves using our JSX framework.

- can access the class on ```j.data.types.TypeBaseObjClass```

```python
class TypeBaseObjClass():

    BASETYPE = "OBJ"
    __slots__ = ['_typebase', '_value']

    def __init__(self,typebase,value=None):

        self._typebase = typebase  #is the factory for this object

        if value is None:
            self._data = 0
        else:
            self._dat = _data_from_init_val(value)

    def _data_from_init_val(self,value):
        """
        convert init value to raw type inside this object
        :return:
        """
        return value

    def _capnp_schema_get(self, name, nr):
        return self._typebase.capnp_schema_get(name,nr)

    @property
    def _string(self):
        raise j.exceptions.NotImplemented()

    @property
    def _python_code(self):
        raise j.exceptions.NotImplemented()

    @property
    def _dictdata(self):
        return self._data

    @property
    def value(self):
        raise j.exceptions.NotImplemented()

    @value.setter
    def value(self,val):
        self._data = self._typebase.toData(val)

    def __str__(self):
        if self._data:
            return "%s: %s"%(self._typebase.__class__.NAME, self._string)
        else:
            return "%s: NOTSET"%(self._typebase.__class__.NAME)

    __repr__ = __str__

```

to check if obj is of this type do

```python
if isinstance(obj,j.data.types.TypeBaseObjClass):
    ...
```
