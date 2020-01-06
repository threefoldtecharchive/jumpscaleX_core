
# ThreeBot Package Manager = Actor

is an actor on threebot, any user with admin rights can call this actor to remotely instruct HIS 3bot to install/remove/start/stop a package
package can be identified by means of git_url
if the package is already on the server (normally not the case) can use the path

```python
def package_add(self, git_url=None, path=None):
    """
    can use a git_url or a path
    path needs to exist on the threebot server
    the git_url will get the code on the server (package source code) if its not there yet
    it will not update if its already there
    """

def package_delete(self, name):
    """
    remove this package from the threebot server
    will call package.uninstall()
    """

def package_stop(self, name):
    """
    stop a package, which means will call package.stop()
    """

def package_start(self, name):
    """
    start a package, which means will call package.start()
    """

def package_upgrade(self, name):
    """
    start a package, which means will call package.start()
    """

```

the package creator needs to fill in ```package.py``` to define how a package gets installed/...

see [package_file.md](package_file.md)

## how to use redis client to add a package

```python
cl = ... a redis connection to the gedis server
#need to authenticate if needed
# see github/threefoldtech/jumpscaleX_core/JumpscaleCore/servers/gedis/tests/4_threebot_redis_registration_encryption.py
cl.execute_command("config_format", "json")  # json or msgpack

data = {}
data["git_url"]="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/phonebook"
data2 = j.data.serializers.json.dumps(data)
data3 = cl.execute_command("default.package_manager.package_add", data2)
data2_return = j.data.serializers.json.loads(data3)
print (data3_return["name"])
```

## how to load a package  using JSX client

```python
cl=j.clients.threebot.client_get(threebot="somebot.ibiza")
#cl=j.clients.threebot.client_get(threebot=10)

# if reload==False then the package will not be reloaded if its already there
cl.actors_all.package_manager.package_add( path=package_path, reload=False)
cl.reload() #this will reload the actors (metadata comes from server)
```

or from giturl

```python
cl.actors_all.package_manager.package_add(
    git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/phonebook",
)
```

when reload is False, which is recommended then the actor packagemanager will not reload the package if already there.
