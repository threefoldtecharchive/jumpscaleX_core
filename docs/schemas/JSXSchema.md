# What is JumpScale Schema

According to wikipedia *"The word schema comes from the Greek word σχήμα (skhēma), which means shape, or more generally,
 plan"*.
In databases "Schema" is some files or some structured code describing the tables and it's fields and data types of each
 field.

JumpScale Schema is a way to define an efficient but yet powerful schemas for your data, Taking advantage of
[capnp's]('https://capnproto.org/language.html') high performance and readability of
[TOML Lang]("https://github.com/toml-lang/toml") combining it with complex data types to achieve both
usability and high performance.

# What do you need to know to define a new schema

## Schema url

The very first part of the schema is the url

> **@url** is the unique locator of the schema , try to have this unique on global basis

> **its good practice to put an version nr at the end of the url**

you can define the schema url like that.
```toml
@url = schema.test.1
```

## basic types

see [types/readme.md]
for the internals of types see [basetypes/readme.md]

## collection types

- L
- e.g. ```LI``` is list of integer
- e.g. ```LS``` is list of string

## collection of other objects

```python
@url =  jumpscale.digitalme.package
name = "UNKNOWN" (S)    #official name of the package, there can be no overlap (can be dot notation)
enable = true (B)
args = (LO) !jumpscale.digitalme.package.arg
loaders= (LO) !jumpscale.digitalme.package.loader

@url =  jumpscale.digitalme.package.arg
key = "" (S)
val =  "" (S)

@url =  jumpscale.digitalme.package.loader
giturl =  "" (S)
dest =  "" (S)
enable = true (B)
```

- generic format ```(LO) !URL```

## enumerators

### are cool, you can store long string representations and they will only take 1 byte to store (shortint)

```
schema = """
    @url = despiegk.test2
    enum = "red,green,blue" (E) #first one specified is the default one
    """
s=j.data.schema.get(schema_text=schema)
o=s.new()
assert o.enum == "RED"
o.enum = 3
assert o.enum == 'RED'  #is always sorted on alfabet

```

### defaults

- ```enable = true (B)```
    - in this case the default is true, so basically everything in between = and (
- ```name = myname (S)``` or ```name = myname```
    - if type not specified the schemas will try to guess the type e.g. Int, String, ...


# How to use schema

```python
schema = """
        @url = despiegk.test
        llist2 = "" (LS) #L means = list, S=String
        nr = 4
        date_start = 0 (D)
        description = ""
        token_price = "10 USD" (N)
        llist = "1,2,3" (LI)
        llist1 = "1,2,3" (L)
        """
```

## format of the schema

```python
@url = despiegk.test.1
llist2 = "" (LS) #L means = list, S=String
nr = 4
date_start = 0 (D)
description = ""
token_price = "10 USD" (N)
cost_estimate:hw_cost = 0.0 #this is a comment
llist = []
llist3 = "1,2,3" (LF)
llist4 = "1,2,3" (L)
llist5 = "1,2,3" (LI)
U = 0.0
pool_type = "managed,unmanaged" (E)
```

## how to get/add a new schema

see [schemas_get_add](schemas_get_add.md)

## how to get a new object (add data using schema)

```python
#using schema url
s=j.data.schema.get(url="jumpscale.digitalme.package") #will die if not exists
#using schema text itself
s=j.data.schema.get(schema_text_path=SCHEMA) #will die if not exists
#create new object
obj = s.new()
obj.abool = True
obj.abool = 1
assert obj.abool == True
obj.abool = 0
assert obj.abool == False
```

> ### can see how the type system we use is intelligent, especially if used for things like numerics.


- for a full example of using schema see the following [test link](https://github.com/threefoldtech/jumpscaleX/tree/development/Jumpscale/data/schema/tests)

## Schema Test

### run all tests

```python
kosmos 'j.data.schema.test()'
```

### run specific test

```python
kosmos 'j.data.schema.test(name="base")'
kosmos 'j.data.schema.test(name="capnp_schema")'
kosmos 'j.data.schema.test(name="embedded_schema")'
kosmos 'j.data.schema.test(name="lists")'
kosmos 'j.data.schema.test(name="load_data")'
```
