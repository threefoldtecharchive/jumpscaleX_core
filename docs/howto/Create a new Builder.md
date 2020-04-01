# How to create a new builder

The aim of this example is to demonstrate how to create a new builder, we will convert a docker file for 
[go-ethereum](https://github.com/ethereum/go-ethereum) by following the official instructions for
building from [source](https://github.com/ethereum/go-ethereum/wiki/Installation-Instructions-for-Ubuntu#building-from-source).

For more details about builders check the [doc](../Internals/builders/Builders.md).

>NOTE: this is an example and will not implement the full builder. Full implementation can be found [here](https://github.com/threefoldtech/jumpscaleX_builders/blob/development/JumpscaleBuildersCommunity/blockchain/BuilderEthereum.py).

## Builder Location

The first thing we will think about is to find the proper location for our builder, which means deciding under which
category should our builder live. Check the available types in `jumpscaleX_builders` repo in our example we will use `JumpscaleBuildersCommunity`.
Second we need to determine which category our builder belongs to, we will use the `blockchain` and under that category we will create our new builder file. Which means the location of our file will be `jumpscaleX_builders/JumpscaleBuildersCommunity/BuilderEthereum.py`.

## Start the Builder class

All builders should inherit from `j.baseclasses.builder` or in certain cases inherit from another builder that is already a child of that class.

To expose the builder to the `j.builders` object you need to specify the `jslocation` to reach this builder.

We will also need to get the `builder_method` decorator that should wrap all the builder methods to perform certain opertions automatically instead of repeating logic in each method.

So the builder class should look something like that:

```python
from Jumpscale import j

builder_method = j.baseclasses.builder_method

class BuilderEthereum(j.baseclasses.builder):
    __jslocation__ = "j.builders.blockchain.geth"
```

The final step is to run `jsx generate` in a JSX installation and from a kosmos shell you should be able to access the new builder as follows:

```python
j.builders.blockchain.geth
```

## Builder tools

Builder tools is a set of tools to perform the common tasks in your builder (e.g read a file , write to a file, execute bash commands and many other handy methods that you will probably need in your builder).
Check [BuilderTools.py](https://github.com/threefoldtech/jumpscaleX_builders/blob/development/JumpscaleBuilders/tools/BuilderTools.py) to see the full list of methods available.

## Builder state

Each builder has its own state manager which can be used to check the state of each method for the builder, we can use
`self._done_set({tag})` to set in the state that this action is done and we can check that using `self._done_check({tag})`.
In most of the cases this is not required since this is done automatically although they can be used to define some extra logic/checks.

If a builder method is called and finished once it will not be called again due to the saved state, if it is required to perform the method again in that case the state can be overriden by setting the `reset` flag to true.

## Implementing methods

The following are the most important methods for a full list check [here](../Internals/builders/Builders.md).

### build

This method should be resposible for building/compiling whatever what is necessary and all the dependencies, we usually have these
types of dependencies:  
1- apt packages: for this we can use `self.system.package.install`  
2- runtimes: like GoLang for example, we have  already implemented builders for the most common languages we are using,
so for GoLang we can use `j.builders.runtimes.go`

In our case we will use golang builder to insure that we have golang installed. It will check the state of golang install and if it is not done will start the install.

It is possible to use GoLang Builder tools to install a go package same as running `go get`. This can be done in the `_init` function to ensure that we have the necessary dependecies before starting buidling.

**NOTE: we don't override `__init__` method in the builder, instead we will implement `_init` method which will be 
called in the end of `__init__` method in the superclass**

```python
def _init(self):
    self.geth_repo = "github.com/ethereum/go-ethereum"
    self.package_path = j.builders.runtimes.go.package_path_get("ethereum/go-ethereum")

@builder_method
def build(self, reset=False):
    """Build the binaries of ethereum
    Keyword Arguments:
        reset {bool} -- reset the build process (default: {False})
    """

    if self._done_check('build') and reset is False:
        return

    j.builders.runtimes.go.install()

    self.get(self.geth_repo)

    self._execute("cd {} && go build -a -ldflags '-w -extldflags -static' ./cmd/geth".format(self.package_path))
    self._execute("cd {} && go build -a -ldflags '-w -extldflags -static' ./cmd/bootnode".format(self.package_path))

    self._done_set('build')

```

### install

This method is responsible for only installing whatever we built on the current system, in our case it will only copy
the built binary to the binary location, we move it to `DIR_BIN` which is equal to`/sandbox/bin` given that in jsx everything should be under `/sandbox/`.

```python
@builder_method
def install(self, reset=False):
    """
    Install the binaries of ethereum
    """
    if self._done_check('install') and reset is False:
        return

    self.build(reset=reset)

     bin_path = self._joinpaths(self.package_path, self._name)
    self._dir_ensure("{DIR_BIN}")
    self._copy(bin_path, self._replace("{DIR_BIN}"))  # _replace method will get the actual bin dir path from `DIR_BIN`

    self._done_set('install')
```

### sandbox

This method should be responsible for collecting all bins and libs and dirs that was a result
of the build and copy it to `DIR_SANDBOX` following the original directory structure.  
for example:  
A binary loacted in `/sanbox/bin/{name}` should be copied to `{DIR_SANDBOX}/sandbox/bin/{name}`

If `flist_create=True` this method should call `self._flist_create(zhub_instance, merge_base_flist)` which is a method
implemented in the base builder class which will tar the sandbox directory and upload it the hub using the provided
zhub instance, with `merge_base_flist` used to specify base flist to merge it with.

```python
@builder_method
def sandbox(
        self,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        if self._done_check('sandbox') and reset is False:
            return

        est_path = self.DIR_SANDBOX
        self.profile_sandbox_select()
        dir_src = self._joinpaths(j.core.dirs.BINDIR, "geth")
        dir_dest = self._joinpaths(dest_path, j.core.dirs.BINDIR[1:])
        self._dir_ensure(dir_dest)
        self._copy(dir_src, dir_dest)
        lib_dest = self._joinpaths(dest_path, "sandbox/lib")
        self._dir_ensure(lib_dest)
        j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

        self._done_set('sandbox')
```

## Startup script

To make the flist autostart once the container is created we can add `startup.toml` to the root of the flist. This should
be as easy as writing a new file inside the `sandbox_dir` so after creating the flist we will have it in the root directory of the flist.
Which is necessary for the instructions in `startup.toml` to run during container startup.
