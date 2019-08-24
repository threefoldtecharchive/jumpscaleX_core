# Gedis backends

This factory is used to get client instances to connect to the backend of the gedis server.

To get a client you need to specify the `type` parameter in the factory `get` method.

To add a client you need to import the client to the factory and add it to `ALLOWED_TYPES` as follows:

```python
from .MyClient import MyClient

ALLOWED_TYPES = {
    'gun': GunClient,
    'myclient': MYCLient
}
```

The key in the above is the type that is used to get the specific client.

## Gundb client

To get a client instance:

```python
client = j.clients.gedis_backend.get('myinstance', type='gun')
```

If the instance doesn't exist you will be prompted to enter the client information, below are the required fields:

- `addr`: address of the server
- `port`: port of the server

Putting data to gun server can be done as follows:

```python
import asyncio
loop = asyncio.get_event_loop()
task = asyncio.async(client.put('new', data=3))
loop.run_until_complete(task)
```

Now to get this data that is already added:

```python
import asyncio
loop = asyncio.get_event_loop()
task = asyncio.async(client.get('new', 'data'))
result = loop.run_until_complete(task) # in that case result = 3
```