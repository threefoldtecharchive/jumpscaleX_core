## Connecting Lapis to Gedis

Gedis is an RPC framework that provide automatic generation of client side code at runtime.
for more info about gedis view [docs](../Gedis/README.md)


To be able to communicate with gedis server from lapis you need to use the following steps:

1 - Create Gedis Actor (i.e. `/tmp/hello.py`)
```python
from Jumpscale import j

class hello(j.application.JSBaseClass):
    def hello_world(self):
        return "Hello World from Gedis"
```

2 - Configure Gedis Server and load the actor before starting the server from kosmos shell
```python
server = j.servers.gedis.configure(name='test', port=8888, host='0.0.0.0')
# load your hello actor
server.actor_add('/tmp/hello.py')
server.start()
```

3 - Configure lapis to be able to connect to gedis server by editing `config.moon` in our quick running lapis repository
```
config = require "lapis.config"

config "development", ->
  gedis_port 8888
  gedis_host '0.0.0.0'
```

4 - Create lapis application to communicate with gedis (i.e. `applications/hello.moon`)
```
lapis = require "lapis"
redis = require 'redis'
config = require("lapis.config").get!
  
class HelloApp extends lapis.Application
  @path: "/hello"
  @name: "hello_"

  [index: ""]: =>
    client = redis.connect(config.gedis_host, config.gedis_port)
    client["gedis"] = redis.command("default.hello.hello_world")
    return client.gedis(client)
```

Note that for using your defined actors methods from redis connector we needed to add it using the following syntax:
`client["gedis"] = redis.command("default.ACTOR.METHOD")`

5 - compile your moon scripts into lua files and start your server
```bash
cd /sandbox/code/github/threefoldfoundation/lapis-wiki/ && moonc . && lapis server
``` 

6 - Try to access your hello page using: `http://localhost:8080/hello`