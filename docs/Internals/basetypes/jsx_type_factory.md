
# jsx type factory

!!!include("types/TypeBaseClasses.py!TYPEBASECLASS",codeblock_type="python")

## CUSTOM class property

if set then [jsx_type_factory.md] will return a specific implementation which will be different depending the speficied default.

this is used to implement e.g. enumeration type.


## basic methods on each factory type class

### clean(val)

-  will convert any possible input to a representation as it can be used in jumpscale environment (not how it will be stored in the DB/capnp)
- e.g. in case of IPAddres its an IPAddressObject()
- e.g. in case of ENUMERATION its an EnumerationObject()
- e.g. in case of a Guid its a string
- e.g. in case of Float its a Float
- will return [basetypes/basetype.md], [jsx_data_obj.md] or [jsx_config_obj.md]

### default_get()

- returns the default value if any as how it will be used in jumpscale environment (see result clean)
- e.g. in case of int:0, float:0.0, ...
- e.g. in case of ENUMERATION = raise Error

### get(**kwargs)

- only implemented where objects can be returned e.g. IPAddress, ENUMERATION, ...
- the object will represent the data format and offer some extra methods e.g. IPAddress will have a ping()
- not done for int, float, ... (all basics)

### check(val)

- if there is a specific implementation e.g. string, float, enumeration, it will check if the input is that implementation
- if not strict implementation or we cannot know e.g. an address will return None

### possible(val)

- will check if it can be converted to the jumpscale representation, basically the clean works without error

### toString()

- representation in a string format
- the clean() needs to be able to use the toString result back to the jumpscale representation we can work with
- its a dense representation in string format

### toData()

- will first to a clean, then will get data out of the resulting object of primitive type
- convert the object to the smallest possible representation in binary
- is stored inside the capnp objects (can be used to store elsewhere as well)

### toHR()  convert to human readable format

- representation in a string format
- the clean() needs to be able to use the toHR result back to the jumpscale representation we can work with
- its the most readable format format, ideal to e.g. represent in screen

### toDict()

- only relevant for types which have a dict representation

### toDictHR()

- same as to dict but the parts are also in HR format

### python_code_get

produce the python code which represents this value

### toml_string_get

will translate to what we need in toml

### capnp_schema_get

will return schema text to be used in definition of capnp schema

