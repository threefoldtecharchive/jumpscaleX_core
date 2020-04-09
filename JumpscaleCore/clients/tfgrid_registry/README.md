# Registry client

Registry is a package that allows the users to cooperate on data as authors, you can control the format of the data to be saved and retrieved with, you can control who can read this data as readers and apply some filters while retrieving the data.

## Package

Check the package docs [here](https://github.com/threefoldtech/jumpscaleX_threebot/blob/development/ThreeBotPackages/tfgrid/registry/wiki/README.md)

**Note** In order to use the client you need to start the package first

## Usage examples

* You need to have a working database with data.

  * Create BCDB database.

    ```python
    db = j.data.bcdb.get("test")
    ```

  * Create a schema and add data to it.

    ```python
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

* create some threebot ids for testing

```python
first_id= j.me.encryptor.tools.me.get("first_id", tid=1, email="test@test.com", tname="first")
second_id= j.me.encryptor.tools.me.get("second_id", tid=10, email="test1@test.com", tname="second")
third_id= j.me.encryptor.tools.me.get("third_id", tid=100, email="test2@test.com", tname="third")
fourh_id= j.me.encryptor.tools.me.get("fourh_id", tid=50, email="test3@test.com", tname="fourth")
fifth_id= j.me.encryptor.tools.me.get("fifth_id", tid=60, email="test4@test.com", tname="fifth")
```

* Register encrypted data

    schema_url = "threebot.registry.test.schema.1"

    ```python
    data_id = j.clients.tfgrid_registry.register(schema = schema, schema_url=schema_url, authors = [first_id.tid, second_id.tid, third_id.tid], model=model,is_encrypted_data = True,readers = [fourh_id.tid, fifth_id.tid])
    ```

* Register non encrypted data

    ```python
    data_id = j.clients.tfgrid_registry.register(schema=schema, schema_url=schema_url, authors=[first_id.tid, second_id.tid, third_id.tid], model=model,is_encrypted_data=False)
    ```

* Get data

    ```python
    author_id = first_id.tid
    data = j.clients.tfgrid_registry.get_data_by_id(data_id, author_id)
    ```

* Get encrypted data for a specific user

    ```python
    author_id = first_id.tid
    data = j.clients.tfgrid_registry.find_encrypted(author_id)
    ```

* Find the non encrypted data with specific format

    ```python
    data = j.clients.tfgrid_registry.find_formatted(registered_info_format = "jsxschema")
    data = j.clients.tfgrid_registry.find_formatted(registered_info_format = "yaml")
    data = j.clients.tfgrid_registry.find_formatted(registered_info_format = "json")
    ```

**Available formats**: `jsxschema`, `yaml`, `json`, `msgpack`, `unstructured`
