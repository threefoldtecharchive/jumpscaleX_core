# Registry client

Registry is a package that allows the users to cooperate on data as authors, you can control the format of the data to be saved and retrieved with, you can control who can read this data as readers and apply some filters while retrieving the data.

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

* Register encrypted data

    ```python
    data_id = j.clients.tfgrid_registry.register(schema = schema, authors = [100,10,1], model = model,is_encrypted_data = True,readers = [50,60])
    ```

* Register non encrypted data

    ```python
    data_id = j.clients.tfgrid_registry.register(schema = schema, authors = [100,10,1], model = model,is_encrypted_data = False)
    ```

* Get data

    ```python
    author_id = 1
    data = j.clients.tfgrid_registry.get_data_by_id(data_id, author_id)
    ```

* Get encrypted data for a specific user

    ```python
    author_id = 1
    data = j.clients.tfgrid_registry.find_encrypted(author_id)
    ```

* Find the non encrypted data with specific format

    ```python
    data = j.clients.tfgrid_registry.find_formatted(registered_info_format = "jsxschema")
    data = j.clients.tfgrid_registry.find_formatted(registered_info_format = "yaml")
    data = j.clients.tfgrid_registry.find_formatted(registered_info_format = "json")
    ```

**Available formats**: `jsxschema`, `yaml`, `json`, `msgpack`, `unstructured`
