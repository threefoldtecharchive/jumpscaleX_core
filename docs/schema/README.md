# What is JumpScale Schema
According to wikipedia *"The word schema comes from the Greek word σχήμα (skhēma), which means shape, or more generally,
 plan"*.  
In databases "Schema" is some files or some structured code describing the tables and it's fields and data types of each
 field.  
JumpScale Schema is a way to define an efficient but yet very powerful schemas for your data, Taking advantage of 
[capnp's]('https://capnproto.org/language.html') high performance and readability of 
[TOML Lang]("https://github.com/toml-lang/toml") combining it with complex data types to achieve both 
usability and high performance.

# What do you need to know to define a new schema

## Schema url
The very first part of the schema is the url, Each schema should have it's unique url over the application.
you can define the schema url like that.  
```toml
@url = schema.test
```
## Data types

| Name | Symbol | Description | sample valid data |
| :----: | :------: | ----------- | --------- |
| String | S | can be any set of characters saved as string | "Hello !" |
| Integer| I | can only be Integer numbers| 1, 2, 200, 1000 |
| Float  | F | just like the primitive float | 1.123, 1.0, 100.99 |
| Boolean| B | can only be True of False | True, False |
| Date   | D | date | 20/11/2018, +4h. see [date supported formats](#date_supported_formats)|
| Numeric| N | can store any numeric data including currencies | 1, 1.12, 10 USD, 90%, 10.5 EUR| 


### <a name="date_supported_formats"></a> Date supported formats
- 0: means undefined date
- epoch = int
- month/day 22:50
- month/day  (will be current year if specified this way)
- year(4char)/month/day
- year(4char)/month/day 10am:50
- year(2char)/month/day
- day/month/4char
- year(4char)/month/day 22:50
- +4h
- -4h

### List support

You can add L before any symbol from the above table to indicate a list  
example: 
```
list_of_floats = (LF) # can accept [1.1, 1.2, 1.3]
list_of_strings = (LS) # can accept ["a", "aa", "aaa"]
```

### Complex data types

you can define more complex data types by nesting schemas  
Example:
```toml
@url = schema.address
street = (S)
floor = (I)
apartment = (I)
```
```toml
@url = schema.student
name = (S)
subjects = (LS)
address = !schema.address
```



