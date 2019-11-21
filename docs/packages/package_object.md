## package object

A package object is remembered in jumpscaleX_core/JumpscaleCore/tools/threebot_package/ThreeBotPackageFactory.py
Its a configuration mgmt object in Jumpscale.

You can only find packages here which have been installed using the 
- [package manager actor in a threebot](package_manager_actor.md)
- the factory: ```j.tools.threebot_packages```

If not initialized yet then cannot find because not configured.

When threebotserver start it will find all known packages and call the start() step.

When threebotserver stops, the same but then stop() for each package.


## Package Object

```python
class ThreeBotPackage(JSConfigBase):
    _SCHEMATEXT = """
        @url = jumpscale.threebot.package.1
        name** = "main"
        giturl = "" (S)  #if empty then local
        path = ""
        threebot_server_name = "default"
        branch = ""
        """

    @property
    def threebot_server(self):
        """
        returns instance of the threebot server which gives access to e.g. the gedis & openresty server
        """
        return j.servers.threebot.get(name=self.threebot_server_name)

    @property
    def gedis_server(self):
        return self.threebot_server.gedis_server

    @property
    def openresty(self):
        return self.threebot_server.openresty_server

    def prepare(self, *args):
        self._package_author.prepare(*args)

    def upgrade(self, *args):
        self._package_author.upgrade(*args)

    def disable(self):
        #still to be implemented

    def start(self):
        ... do all std actions when starting a package (see below)
        self._package_author.start()

    def stop(self):
        self._package_author.stop()

    def uninstall(self):
        self._package_author.uninstall()
```

- property ```_package_author``` 
    - is the package_file obj as described in [package file](package_file.md)
    - basically it calls the lifecycle management methods as created by the package creator

## what is done automatically when starting a package

### find models

- see if ```$PACKAGEDIR/models/``` exists
  - if yes call: 
    - ```self.bcdb.models_add(path=self.package_root + "/models")```
- see ```$PACKAGEDIR/actors/``` exists
  - if yes
    - ```self.gedis_server.actors_add(path, namespace=self._package_author.actors_namespace)```
- will also load:
  - chatflows
      - interactive communication, implemented as chat bots
      - each file inside is a chat bot
  - docsites
      - markdown documentation sites, published under /wiki/$docsite_prefix/...
      - each subdir is a docsite
  - docmacros
      - macro's as used in docsite(s)
      - each file inside is a docmacro (can be in subdirs)
  - wiki
  - html
