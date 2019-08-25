
# j.application.JSBaseConfigsParent

Is the base class for a collection of config objects,
that can have a child class (e.g. another `JBaseConfigs` class),
such that the child instances created have also access to the config of the parent class.

## Example

```python
class TFChainWallet(j.baseclasses.object_config):
    """
    Tfchain Wallet object
    """
    _SCHEMATEXT = """
        @url = jumpscale.tfchain.wallet
        name* = "" (S)
        """
    @property
    def network_type(self):
        return self._parent._parent.network_type

class TFChainWalletFactory(j.baseclasses.factory):
    # see configs.md to learn more about the JSBaseConfigsClass
    """
    Factory class to get a tfchain wallet object
    """
    _CHILDCLASS = TFChainWallet
    _name = "wallets" # see configs.md for more information about this property

class TFChainClient(j.application.JSBaseConfigParentClass):
    """
    Tfchain client object
    """
    _SCHEMATEXT = """
        @url = jumpscale.tfchain.client
        name* = "" (S)
        network_type = "STD,TEST,DEV" (E)
        """

    _CHILDCLASSES = [TFChainWalletFactory]

class TFChainClientFactory(j.baseclasses.factory):
    """
    Factory class to get a tfchain client object
    """
    __jslocation__ = "j.clients.tfchain"
    _CHILDCLASS = TFChainClient
```

With this setup `Wallet` instances can than access the config of the parent client as well:

```bash
$ kosmos 'print(j.clients.tfchain.foo.wallets.bar.network_type)'
STD

$ kosmos 'print(j.clients.tfchain.new("foo", network_type="TEST").wallets.bar.network_type)'
TEST
```
