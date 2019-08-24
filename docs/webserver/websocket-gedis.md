## Connecting to Gedis over websockts

Gedis server has no direct way for conecting to it through browser, so we can use openresty websocket server as a proxy layer between browser and Gedis 


To be able to communicate with gedis server from html using websockets you need to use the following steps:

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

3 - Go to our quick running lapis repository [lapis-wiki] to configure lapis to be able to connect to gedis server by editing `config.moon` file. 
```
config = require "lapis.config"

config "development", ->
  gedis_port 8888
  gedis_host '0.0.0.0'
```

4 - compile your moon scripts into lua files and start your server
```bash
cd /sandbox/code/github/threefoldfoundation/lapis-wiki/ && moonc . && lapis server
``` 

5 - Make sure to get static files from jumpscale_weblibs repo
```python
url = "https://github.com/threefoldtech/jumpscale_weblibs"
weblibs_path = j.clients.git.getContentPathFromURLorPath(url)
j.sal.fs.symlink("{}/static".format(weblibs_path), "{}/static/weblibs".format(server_path), overwriteTarget=False)
```

6 - Create your html file that will include [Gedis client](https://raw.githubusercontent.com/threefoldtech/jumpscale_weblibs/master/static/gedis/gedis_client.js)
```html
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Gedis Test</title>
        <script>const SERVER='ws://localhost:8080/ws';</script>
        <script src='http://localhost:8080/static/weblibs/gedis/gedis_client.js'></script>
    </head>
    <body>
        <script>
            const EXEC_OBJ = {
                "namespace": "default",
                "actor": "hello",
                "header": {"response_type": "json"},
                "command": "hello_world"
                // You can pass arguments too if your actor method needs
                // "args": {"arg1":"value1"}
            }
            GEDIS_CLIENT.execute(EXEC_OBJ).then(function(res){
                alert(res)
            });
        </script>
    </body>
</html>
```

7 - Try to open this html file using the file system or served from any web server
