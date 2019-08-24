# BCDB
BCDB `Block Chain Database` is a Database built with `Block Chain` concepts. 

## Components
### Models 
the model in BCDB is a class using [JumpScale Schema](/docs/schema/README.md) it adds:
- indexing capabilities 
    - to make data queries go faster you can use indexing with BCDB to the fields you will query with,
 this can be achieved easily by just adding `*` beside the field you want to index in the schema 
        ```
        @url = school.student
        name* = (S)
        subjects = (LS)
        address = !schema.address
        ```
        _if you are not familiar with the [JumpScale Schema](/docs/schema/README.md), it's highly recomended to read
        the schema documentation before proceeding to this part_  
        in the previous schema `name` will be indexing, we will demonstrate how to use that to do a query in the usage
        section
- Hooks
    - you can add hooks to be manipulated before set/get

### Namespaces
to organize the models stored in the database, the database is divided into namespaces, the default namespace is called 
`default`

### Backend
in order to get BCDB to work you should provide a Backend client, A `Backend Client` is a `Jumpscale client` 
for a key value store (ZDB, Redis or ETCD) which will be used to save the data

## Usage
```python
# Define the Schema
schema = """
        @url = school.student
        name* = (S)
        subjects = (LS)
        address = (S)
        """
# Get DB client (we will use zdb test server to start and get zdb client)
db_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)

# Get BCDB databse object
db = j.data.bcdb.get(db_cl,namespace="test",reset=True)

# Create a BCDB model with the previous schema
model = db.model_create(schema=schema)

# Create a new object from the model
o = model.new()

# Fill data 
o.name = "foo"
o.subjects.append("math")
o.subjects.append("science")
o.address = "2 bar street"

# Save object to database
saved_object = model.set(o)

# Now you can get Object with ID
loaded_object = model.get(saved_object.id)

# To query using the indexed fields
qres = model.index.select(model.index.name == "foo")

# IMPORTANT NOTE :
# the query result will contain only the id and the indexed fields
# if you want to get the full model you need to get it fom the model using the ID
queried_object = model.get(qres[0].id)
```
## add models from path 

```
# Get DB client (we will use zdb test server to start and get zdb client)
db_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)

# Get BCDB databse object
bcdb = j.data.bcdb.get(db_cl,namespace="test",reset=True)

#by default add models and load it to search stored information using the index defined in the schema
bcdb.models_add("/sandbox/code/github/threefoldtech/digitalmeX/packages/notary/models") 


```
