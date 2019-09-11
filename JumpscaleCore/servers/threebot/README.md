# Threebot server 
Threebot server is designed to be your own digital self, you can host content, sites and even complex applications very easily

## how to start 
### Basic threebot
```bash
kosmos 'j.servers.threebot.get("3bot_name").start(web=False, ssl=False)'
```
this will start the basic threebot server which will have:
- [gedis server](https://github.com/threefoldtech/jumpscaleX_core/blob/development/docs/Gedis/README.md) with base actors loaded
- [zdb server](https://github.com/threefoldtech/0-db/blob/development/README.md)
- [sonic server](https://github.com/valeriansaliou/sonic/blob/master/README.md) (used for full text indexing)

### threebot for web
```bash
kosmos 'j.servers.threebot.get("3bot_name").start(web=True, ssl=False)'
```
this will start the basic servers in addition to servers that will be needed to host a web application
- [openresty server](https://github.com/threefoldtech/jumpscaleX_core/blob/development/JumpscaleCore/servers/openresty/README.md) 
- [threebot bottle server]() a bottle server to serve the content of [bcdbfs](https://github.com/threefoldtech/jumpscaleX_core/blob/development/JumpscaleCore/sal/bcdbfs/README.md) as static files 
- websocket proxy server for gedis server

### threebot for web with ssl
```bash
kosmos 'j.servers.threebot.get("3bot_name").start(web=True, ssl=True)'
```
this will start the same threebot for web server with ssl configured


## Packages
packages is how you tell your threebot what to serve and how

### How to create a new package
threebot package is class that inherits from `j.baseclasses.threebot_package` and implement the following methods
```
from Jumpscale import j


class Package(j.baseclasses.threebot_package):
    def prepare(self):
        """
        is called at install time
        :return:
        """
        pass

    def start(self):
        """
        called when the 3bot starts
        :return:
        """
        pass
        
    def stop(self):
        """
        called when the 3bot stops
        :return:
        """
        pass

    def uninstall(self):
        """
        called when the package is no longer needed and will be removed from the threebot
        :return:
        """
        pass

```

## How to load a package
after creating your package you can load it so it can be started when your threebot start
```python
j.tools.threebot_packages.get("package_name", 
                            git_url="{git url if it's not local}", 
                            path="{path to your local package}" ,
                            threebotserver_name="{threebot server name}")
```

## Example packages
- [pastebin](https://github.com/threefoldtech/jumpscaleX_threebot/blob/development/ThreeBotPackages/pastebin/README.md
)
- [alerta](https://github.com/threefoldtech/jumpscaleX_threebot/blob/development/ThreeBotPackages/alerta/README.md)
- [myjobs](https://github.com/threefoldtech/jumpscaleX_threebot/blob/development/ThreeBotPackages/myjobs/README.md)

## Troubleshooting

if you encounter an error after launching the threebot make sure that you have the latest code on all the repository (libs,libs_extra, threebot, builders, jsx_core)
and run this comand to gather all the locations and builds the j object tree
```shell
3bot:~: jsx generate
```
