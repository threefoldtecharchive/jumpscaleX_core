# ZDB Client
A jumpscale client for [ZDB](https://github.com/threefoldtech/0-db), if you are not familiar with ZDB please read the docs first

## ZDB Running Modes:
Check ZDB Running Modes [here](https://github.com/threefoldtech/0-db#running-modes) to know the differences between modes, you should specify the running mode when you get a zdb client in order to get a client compatible to your zdb server.
**Examples:**
*Sequential mode client:*
```python
sequential_client = j.clients.zdb.client_get(name="main", namespace="mynamespace", addr="localhost", port=9900, secret="1234", mode="seq")
```
*User mode client:*
```python
user_client = j.clients.zdb.client_get(name="main", namespace="mynamespace", addr="localhost", port=9900, secret="1234", mode="user")
```
*Direct mode client:*
```python
direct_client = j.clients.zdb.client_get(name="main", namespace="mynamespace", addr="localhost", port=9900, secret="1234", mode="direct")
```

## Client Usage Example:
```
zdb_client = j.clients.zdb.client_get(name="main", namespace="mynamespace", addr="localhost", port=9900, secret="1234", mode="seq")
zdb_client.set(key="key", data="data")
zdb_client.get("key") # == "data"
# to iterate over all keys in this namespace
zdb_client.iterate()
# to iterate over all keys in this namespace starting from a key
zdb_client.iterate(start_key="key")
```

## Admin client:
the admin client is used to manage [ZDB Namespaces](https://github.com/threefoldtech/0-db#namespaces)
**Example**
```python
admin_client = j.clients.zdb.client_admin_get(name="main", addr="localhost", port=9900, secret="1234", mode="seq")
# list namespaces
namespaces = admin_client.namespaces_list()

# create namespace
admin_client.namespace_new(name="foo", secret="bar")

# get client for a namespace
admin_client.namespace_get(name="foo", secret="bar")
```
