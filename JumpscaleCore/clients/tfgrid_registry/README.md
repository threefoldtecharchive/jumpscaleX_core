# Registry client
Registry is a package that allows the users to cooperate on data as authors, you can control the format of the data to be saved and retrieved with, you can control who can read this data as readers and applying some filters while retrieving the data.

## usage examples
* You need to have working database with data.

Create BCDB database.
```
j.data.bcdb.new("test")
db = j.data.bcdb.get("test")
```
Create schema and add data to it.
```
schema = """
            @url = threebot.registry.test.schema.1
            url = "" # unique url, points to where the wiki is
            description = ""
            topic = "travel,food,it" (E)
            tags = (LS)
        """

scm = j.data.schema.get_from_text(schema)
model = db.model_get(url=scm.url).new()
model.url = "testwikis.com"
model.description = "this is a test wiki about travel"
model.tags = "travel, hotels, diving"
model.save()
```

* Register encrypted the data
```
data_id = j.clients.tfgrid_registry.register(schema = schema, authors = [100,10,1], model = model,is_encrypted_data = True,readers = [50,60])
```
* Register not encrypted data
```
data_id = j.clients.tfgrid_registry.register(schema = schema, authors = [100,10,1], model = model,is_encrypted_data = False)
```

* Get data
```
data = j.clients.tfgrid_registry.get_data_by_id(data_id,author_id)
```

* Get encrypted data for a specific user
```
data = j.clients.tfgrid_registry.find_encrypted(author_id)
```

* Find the not encrypted data with specific format
```
data = j.clients.tfgrid_registry.find_formatted(registered_info_format = "jsxschema")
data = j.clients.tfgrid_registry.find_formatted(registered_info_format = "yaml")
data = j.clients.tfgrid_registry.find_formatted(registered_info_format = "json")
```
**available formats**: jsxschema,yaml,json,msgpack,unstructured
