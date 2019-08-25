
## Factory Base Class

Can have a `__jslocation__`, meaning it will be attached somewhere in the `Jumpscale` namespace.

It can optionally be a container for one or more config classes,
that is why it is not `_CHILDCLASS `here but `_CHILDCLASSES`.

```python
from Jumpscale import j

class World(j.application.JSBaseConfigsFactoryClass):
    """
    some text explaining what the class does
    """

    __jslocation__ = 'j.data.world'

    _CHILDCLASSES = [Cars,Ships]


class Cars(j.baseclasses.factory):
    """
    ...
    """
    _CHILDCLASS = Car


class Car(j.baseclasses.object_config):
    """
    one car instance
    """

    _SCHEMATEXT = """
        @url = jumpscale.example.car.1
        name* = ""
        city = ""
        """

    def _init(self):
        pass



class Ships(j.baseclasses.factory):
    """
    ...
    """
    _CHILDCLASS = Ship


class Ship(j.baseclasses.object_config):
    """
    one ship instance
    """

    _SCHEMATEXT = """
        @url = jumpscale.example.ship.1
        name* = ""
        location = ""
        onsea = true (b)
        """

    def _init(self):    
        pass


```

The `_CHILDCLASSES` are one or more config(s) classes, always defined as a (Python) List.

A `childclass` can be a singleton (means just add a JSConfig class)
