# Gedis

Gedis is a RPC framework that provide automatic generation of client side code at runtime.
Which means you only need to define the server interface and the client will automatically receive the code it needs to talk to the server at connection time.

Currently we support client generation for python and javascript.

Gedis can works directly on top a of a tcp connection or over websocket if a web proxy is available (openresty, caddy,...)
The data may be binary encoded using capnp or not during transfer, it is decided based on the client need
The communication protocol used is [RESP](https://redis.io/topics/protocol)

## Actors

The RPC interface is defined by creating a python class. All the public methods of the class will be exposed as remote RPC call that clients can call. We name such a class an `actor`.

### Actor methods

An actor method signature can have no or multiple arguments.
If you don't need any type validation, you can just use normal arguments. example:

```python
def foo(arg1, arg2):
    result = do_smth(args1, args2)
    return result
```

This actor method will receive what is sent by the client without any data format validation. The user needs to validate the data format manually.

If you want to enforce data validation automatically, click [here](../schemas/README.md) for more details on schemas and refer to [types](../types/README.md) for supported types.
To define which schema is expected you need to write a docstring to your method. example:

```python
def foo(self, wallet, schema_out=None, user_session=None):
    """
    ```in
    wallet = (O) !jumpscale.test.ibiza.wallet
    ```

    ```out
    !jumpscale.test.ibiza.wallet
    ```
    """
    w = schema_out.new()

    w.ipaddr = wallet.ipaddr
    w.addr = wallet.addr
    w.jwt = wallet.jwt
    return w
```

This actor method has 3 arguments, `wallet`, `schema_out` and `user_session`. With the docstring we ask gedis to validate that `wallet` is actually a valid instance of the schema named `jumpscale.test.ibiza.wallet`. We also define the type of the return value with the `schema_out` argument and the docstring which specify that schema_out is also an instance of the `jumpscale.test.ibiza.wallet`.

When defining docstring like this, if the data received or sent back doesn't validate the schema, an error will be raised.

## Automatic client generation

Gedis doesn't requires to generate client stub or anything like that. During the connection, the client will receive the generated code for the actor from the server directly.
This make the deployment and update of you client really easy since you don't have to give specific client code to your users. All the magic happens transparently when you connect to a server.

## Quick start

### Define server interface

Creation of an actor at `/tmp/actor.py`:

```python
from Jumpscale import j

class actor(j.baseclasses.threebot_actor):

    def _init(self, **kwargs):
        pass

    def ping(self):
        return "pong"
```

Creation of the gedis service and load our actor:

```python
# configure the server
server = j.servers.gedis.get(name='test', port=8889, host='0.0.0.0', ssl=False)
# load a single actor
server.actor_add('/tmp/actor.py', namespace='demo')
# you can also load a directory that contains multiple actor files
# let's imagine you have a directory structure like
# tree test_actor/
# test_actor/
# ├── actor2.py
# ├── actor.py
# you can load all the actors with
server.actors_add('/tmp/test_actor', namespace='demo')

# start the server
server.save()
server.start()
```

### Get a python client

```python
# create a client
# during the connection, the client will receive the generated code for the actor
client = j.clients.gedis.new(name='test', host='192.168.10.10', port=8889, ssl=False)

# use the client
client.actors.actor.ping() # note if your actor name is xactor, then client.actors.xactor.ping()
# result will be b'pong'

```

to get a client for a specific package you can pass the package name to gedis client get method, this will only load actors from this package
Example:
```
client = j.clients.gedis.new(name='test', host='192.168.10.10', port=8889, ssl=False, package_name="zerobot.base")
```
**to see more usage examples please read the tests in [gedis_factory class](https://github.com/threefoldtech/jumpscaleX_core/blob/development/JumpscaleCore/servers/gedis/GedisFactory.py)**
