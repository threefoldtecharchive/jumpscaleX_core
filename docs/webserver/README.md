## Webserver

To be able to serve websites we are using [lapis](http://leafo.net/lapis/) web framework which is built depending on [openresty](https://openresty.org) + nginx.

It enables us to write nginx scripts using lua with high performance. You will need firstly to [install JumpscaleX with lua and openresty option](https://github.com/threefoldtech/jumpscaleX/tree/development/install) 

### Starting your first lapis app
We have a quick running repository for lapis project which contains our main configurations, static files, system apps, ... etc

1 - To clone this repo you will need to run the following in kosmos shell:
```python
# this will clone the lapis project into /sandbox/code/github/threefoldfoundation/lapis-wiki
url = "https://github.com/threefoldfoundation/lapis-wiki"
server_path = j.clients.git.getContentPathFromURLorPath(url)

# optional: if you need to have static weblibs from our repos
url = "https://github.com/threefoldtech/jumpscale_weblibs"
weblibs_path = j.clients.git.getContentPathFromURLorPath(url)
j.sal.fs.symlink("{}/static".format(weblibs_path), "{}/static/weblibs".format(server_path), overwriteTarget=False)
```

2 - Create your first application (i.e. `hello.moon`) into applications directory `/sandbox/code/github/threefoldfoundation/lapis-wiki/applications` or create it in any directory and soft link it into the application dir

```bash
touch /sandbox/code/github/threefoldfoundation/lapis-wiki/applications/hello.moon
```

3 - Implement you webservice logic into hello.moon using moon script
```
lapis = require "lapis"
  
class HelloApp extends lapis.Application
  @path: "/hello"
  @name: "hello_"

  [index: ""]: =>
    "Hello World"
```

4 - compile your moon scripts into lua files and start your server
```bash
cd /sandbox/code/github/threefoldfoundation/lapis-wiki/ && moonc . && lapis server
```

5 - Try to access your hello page using: `http://localhost:8080/hello`

### What's next

- Use lapis to communicate with gedis server [tutorial](lapis-gedis.md)
- Use openresty as a websocket server to communicate with gedis server from javascript [tutorial](websocket-gedis.md)
 