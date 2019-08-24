# Threebot server 
Threebot server is designed to be your own digital self, you can host content, sites and even complex applications very easily

## how to start 
```bash
kosmos 'j.servers.threebot.get("3bot_name").start()'
```

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
j.tools.threebotpackage.get("package_name", 
                            git_url="{git url if it's not local}", 
                            path="{path to your local package}" ,
                            threebotserver_name="{threebot server name}")
```
