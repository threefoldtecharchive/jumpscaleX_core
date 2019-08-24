
# String

## list string

can be represented as string with comma's eg ```1,2,3,4``` or ```jan,piet ,pol```
there can be spaces inside, they are ignored

[] can be used as well

### List supports subtypes

You can add L before any symbol from the above table to indicate a list  

# example: 
```python
list_of_floats = (LF) # can accept [1.1, 1.2, 1.3]
list_of_strings = (LS) # can accept ["a", "aa", "aaa"]
list_of_multiLines =  (Lmultiline) # can accept ["example \\n example2 \\n example4", "example \\n example2 \\n example3"]
list_of_guids = (Lguid) # can accept ['bebe8b34-b12e-4fda-b00c-99979452b7bd', '84b022bd-2b00-4b62-8539-4ec07887bbe4'] 

```
```python
 SCHEMA = """
        @url = test.schema
        email_list = (Lemail)
        list_emails = ['test.example@domain.com' ,"test.example2@domain.com"] (Lemail)
        """
schema = j.data.schema.get(SCHEMA)
schema_obj = schema.new()
schema_obj.email_list = ["test@example.com"]
```
```python
SCHEMA2 = """
        @url = test.schema.2
        port_list = (Lipport)
        list_ports = [3164, 15487] (Lipport)
        """
schema = j.data.schema.get(SCHEMA2)
schema_obj = schema.new()
schema_obj.port_list = [80,443,2379]
```
