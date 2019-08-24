# How to create a new builder

The aim of this example is to demonstrate how to start a new builder, we will convert a docker file for 
[go-ethereum](https://github.com/ethereum/go-ethereum) to a builder, we will follow the official instructions for 
building from source [here](https://github.com/ethereum/go-ethereum/wiki/Installation-Instructions-for-Ubuntu#building-from-source)

**NOTE: this is an example and will not implement the full builder**

## Builder Location
the first thing we will think about is to find the proper location for our builder, which means deciding under which 
category should our builder live.  
in our case we will create it under `/jumpscale/builder/blockchain` so we will create a new file call it 
`BuilderEthereum.py`.  
and now to make this builder accessible from Jumpscale object we should register it in the category factory, 
The factory name will be in this format `Builder{category_name}Factory`, so in our case the factory is 
`BuilderBlockchainFactory.py`, we will open this file and add the following lines to the `init` of the factory

```python
from .BuilderEthereum import BuilderEthereum
self.ethereum = BuilderEthereum()
```
and now the builder will be accessible from `j.builders.blockchain.ethereum`

## Start the Builder class
 All builders should inherit from `j.builders.system.BaseClass` and it should have the Property `Name` set, we will use 
 this property later in the builder, and Now our builder class should look like this
 ```python
from Jumpscale import j

class BuilderEthereum(j.builders.system._BaseClass):
    NAME = "geth"
``` 

## Builder tools 
Builder tools is a set of tools to perform the common tasks in your builder (e.g read a file
, write to a file, execute bash commands and many other handy methods that you will probably need in your builder)
Check [BuilderTools.py](https://github.com/threefoldtech/jumpscaleX/blob/development/Jumpscale/builder/tools/BuilderTools.py)
 to see the full list of methods available 
 
## Builder state
Builders have it's own state manager which can be used to check the state for each method for the builder, we can use 
`self._done_set({tag})` to set in the state that this action is done and we can check that using `self._done_get({tag})` 

## Implementing methods

### build(self, reset=False)
This method should be resposible for building whatever I want to build and all the dependencies, we usually have these 
types of dependencies:  
1- apt packages: for this we can use `self.tools.package install`  
2- runtimes: like GoLang for example, we have  already implemented builders for the most common languages we are using, 
so for GoLang we can use `j.builders.runtimes.go`

in our case we will use golang builder to insure that we have golang installed and if not we install it,
we can also use GoLang Builder tools to install a go package like from `go get` and that will be the build and _init 
method in this step

**NOTE: we don't override `__init__` method in the builder, instead we will implement `_init` method which will be 
called in the end of `__init__` method in the superclass**

```python
def _init(self):
    self.geth_repo = "github.com/ethereum/go-ethereum"
    self.package_path = j.builders.runtimes.golang.package_path_get("ethereum/go-ethereum")


def build(self, reset=False):
    """Build the binaries of ethereum
    Keyword Arguments:
        reset {bool} -- reset the build process (default: {False})
    """

    if self._done_get('build') and reset is False:
        return

    if not j.builders.runtimes.golang.is_installed:
        j.builders.runtimes.golang.install()

    j.builders.runtimes.golang.get(self.geth_repo)

    j.builders.runtimes.golang.execute("cd {} && make geth".format(self.package_path))
    self._done_set('build')

```

### install(self, reset=False)

this method is responsible for only installing whatever we built on the current system, in our case it will only copy 
the built binary to the binary location, we move it to `/sandbox/bin` given that in jsx everything should be under `/sandbox/` 

```python
def install(self, reset=False):
    """
    Install the binaries of ethereum
    """
    if self._done_get('install') and reset is False:
        return

    self.build(reset=reset)

    bin_path = self.tools.joinpaths(self.package_path, "build", "bin", "geth")
    self.tools.file_copy(bin_path, "/sandbox/bin")
    self._done_set('install')
```

### sandbox(sandbox_dir="/tmp/builder/{name}", flist=True, zhub_instance=None)

this method should be responsible for collecting all bins and libs and dirs that was a result
of the build and copy it to `destination_dir` in the same directory structure.  
example:  
a binary loacted in `/sanbox/bin/{name}` should be copied to `{destinatrion_dir}/sandbox/bin/{name}`

then if `flist=True` this method should call `self.flist_create(sandbox_dir,zhub_instance)` which is a method 
implemented in the base builder class which will tar the sandbox directory and upload it the hub using the provided 
zhub instance

```python
def sandbox(self, sandbox_dir="/tmp/builder/ethereum", flist=False, hub_instance=None, reset=False):
        if self._done_get('sandbox') and reset is False:
            return

        self.build(reset=reset)
        bin_path = self.tools.joinpaths(self.package_path, "build", "bin", "geth")
        bin_dest = self.tools.joinpaths(sandbox_dir, 'sandbox', 'bin')
        self.tools.dir_ensure(bin_dest)
        self.tools.file_copy(bin_path, bin_dest)

        if flist:
            print(self.flist_create(sandbox_dir=sandbox_dir, hub_instance=hub_instance))

        self._done_set('sandbox')
```

## Startup script
To make the flist autostarts once the container created we can add `startup.toml` to the root of the flist, this should 
be as easy as writing a new file inside the `sandbox_dir` so after flisting we will have it in the root of the flist.


**The full implementation for this builder can be found 
[here](https://github.com/threefoldtech/jumpscaleX/blob/development_builders/Jumpscale/builder/blockchain/BuilderEthereum.py)**
