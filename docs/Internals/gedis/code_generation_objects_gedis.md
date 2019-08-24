# information fed into the templates

obj is actormeta

```python
#actormeta
class GedisCmds():      #is from gedis server
    name                #is name of the actor
    namespace           #namespace of the actor
    cmds = {name:cmd}   #cmd is the GedisCmd
```

```python
#cmd
class GedisCmd():       #is from gedis server
    name                #is name of the cmd (method on the actor)
    namespace           #namespace of the actor    
    schema_in           #Schema() or None if no schema
    schema_out          #Schema() or None if no schema
    args                #is text representation of what needs to come in method for the server
                        #e.g. method(something=...) in between the ()
    args_client         #same as args but for python client
    args_client_js      #same as args but for javascript client
    cmdobj              ## is resulting obj from = metadata in JSX obj format of the actor method
                        #@url = jumpscale.gedis.cmd
                        #name = ""
                        #comment = ""
                        #schema_in = ""     is the url to the schema
                        #schema_out = ""    is the url to the schema
                        #args = (ls)        list of arguments of the actor method

    code_indent         #4 char intended code from self.cmdobj.code
    comment_indent      #4 char intended code from self.cmdobj.comment
    comment_indent2     #8 char intended code from self.cmdobj.comment
    

```

```python
#cmd
class Schema():         #is from j.data.schema
    url
    key                 #url in format which can be used as key no . and all lower case & dense
    text                #the text of the schema
    
    properties          #list of SchemaProperty objects
    
    properties_index_sql    #list of properties which are used in the index for sqlite
    properties_index_keys   #list of properties which are used in the index for redis
    propertynames           #list of property names

```

```python
#cmd
class SchemaProperty(): #is from j.data.schema
    name                #name of the property
    name_camel
    comment             #comment of property if any
    index               #bool: is True if used in sqllite indexing
    index_key           #bool: is True if used as index of names in redis
    unique              #bool: is True if unique in the table
    jumpscaletype       #is a jumpscale type as used in j.data.types
    js_typelocation     #is the location of the jumpscale type
    default             #default as given by jumpscaletype  (is in a jumpscale obj format)
    default_as_python_code  #default but not usable as python code (easier to generate with)



```



```python
#cmd
class JumpscaleType():  #is from j.data.types
    BASETYPE                #basetype used to build this from
    NAME                    #name of the type e.g. int

    def check(self, value):
    def possible(self, value): #can it be converted to this type
    def fromString(self, txt):
    def toJSON(self, v):
    def toString(self, val):
    def python_code_get(self, value):

    def toHR(self, v):
    def toDict(self,v):
    def toDictHR(self,v):
    def toData(self, v):  #data of capnp, what needs to be used for sending over wire as well


    def toml_string_get(self, value, key=""):
    def capnp_schema_get(self, name, nr):

    def clean(self, v):         #returns python primitive type or JumpscaleTypeObject
    def default_get(self):      #returns python primitive type or JumpscaleTypeObject

```
more info see [jsx_type_factory.md]

after clean you have a JumpscaleTypeObject

```python
#cmd
class JumpscaleTypeObject():  #is from j.data.types  see TypeBaseObjClass
    _typebase       # is the JumpscaleType() which generates this one
    _string         # convert to string
    _data           # the internal representation
    _python_code    # how to express as python code
    _dictdata       # data as how it needs to be used in a dict representation is the _data
    value           #setter & getter to get info in & out of object

```