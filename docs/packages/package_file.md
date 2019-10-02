# package file

is the package.py file which is read when a package get's loaded.

This is the ONLY file which deals with installing, start/stop, remove a package from a 3bot.

Please do not put any load/install/uninstall logic on any other location.

```python
class Package(j.baseclasses.threebot_package):

    def _init(self, **kwargs):
        #if you want to initialize something you might need for your package, is optional !!!
        self.actors_namespace = "someothernamespace" #default is 'default' can overrule like this
        self.giturl = ...

    @property
    def bcdb(self):
        #is the default implementation, if you want to overrule, provide this method
        return self.threebot_server.bcdb_get("system")

    def prepare(self):
        """
        is called at install time
        :return:
        """
        #use this to e.g. checkout git files use
        codepath = j.clients.git.getContentPathFromURLorPath(urlOrPath=self.giturl, pull=True, branch=None):
        #e.g. when you have developed a website can use this to check out the git code
        #the codepath will be where the code is checked out        
        #can now e.g. 

    def upgrade(self):
        """
        used to upgrade
        """
        codepath = j.clients.git.getContentPathFromURLorPath(urlOrPath=self.giturl, pull=True, branch=None):
        #note pull is True here
        #std is to call prepare again, if nothing filled in

    def start(self):
        """
        called when the 3bot starts
        :return:
        """
        #std will load the actors & models & the wiki's, no need to specify
        #can add anything else which could be relevant
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
        # TODO: clean up bcdb ?
        pass
```

what will the package loader in 3bot automatically do?

- every time a threebot starts it will walk over all known packages and start them

## properties available in the package object

```python
self.package_root =     #path of this dir
self.gedis_server =     #gedis server which will serve actors in this package
self.openresty =        #openresty which is active in the threebot server
self.threebot_server =  #the threebot server itself
self.rack_server =      #the gevent rackserver dealing with all gevent greenlets running in a gevent rack
self.bcdb =             #can be overruled by you (is a property), default is the system bcdb
```

