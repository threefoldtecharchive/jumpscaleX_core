# j.data.types

Is our factory to work with jumpscale types

there are 2 types of factories

- factory base type class is 
    - e.g. j.data.types.string will produce primitive type (which is default supported python object e.g. int, bool, string, ...)
  
- factory jsx type class
    - e.g. j.data.types.numeric will produce jsx type e.g. numeric which is a [jsx_type obj](jsx_type_obj.md) 
    - jsx type obj exists in 3 sorts
        - [jsx_type obj](jsx_type_obj.md) is a type which is implemented in JSX is implemented in j.data.types e.g. ipaddress, numeric, ...
        - [jsx_data obj](jsx_data_obj.md) is a complex type as result of [JSX schemas](schemas/README.md)
        - [jsx_config obj](jsx_config_obj.md) is a config type as result of using j.data.config


## the factories

see [jsx_type_factory.md]

