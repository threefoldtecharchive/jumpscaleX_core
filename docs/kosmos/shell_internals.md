# Shell internals
You'll find a description on how every part of our custom shell was implemented.

[ptpython](https://github.com/prompt-toolkit/ptpython) uses [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/en/stable/), so, when we mention internals, it's mostly related to the prompt-toolkit application (like containers, layout...etc) and it's better to explore this docs before going through this document.

The start point for our modifications is the configration function of `ptpython`,  we use `embed()` of `ptpython.repl`, which can take a configure function that takes `repl` as a [PythonRepl](https://github.com/prompt-toolkit/ptpython/blob/master/ptpython/repl.py#L42) object:


```python
from ptpython.repl import embed

def config(repl):
    ...


embed(globals_, locals_, configure=config)
```


We've defined `ptconfig()` in [KosmosShell.py](https://github.com/threefoldtech/jumpscaleX_core/blob/development/JumpscaleCore/core/KosmosShell.py), where we apply some monkey patching and updates to this repl.


### Content

- [Registering key bindings](#registering-key-bindings)
- [Updating Layout](#updating-layout)
- [Custom fitlers](#custom-filters)
- [Auto-Completion](#auto-completion)
- [Docstrings](#docstrings)
- [Exceptions and logging](#exceptions-and-logging)

## Registering key bindings

We use `repl.add_key_binding` decorator to register a key-binding, before adding any one, make sure it's not already registered, see [ptpython.key_bindings](https://github.com/prompt-toolkit/ptpython/blob/master/ptpython/key_bindings.py), for example, `Control + J` is for debugging:

https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L360-L376

See [more about prompt-toolit key bindings](https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/key_bindings.html).


## Custom filters
We define some custom fitlers that we use inside layouts and key bindings, filters are just prompt-toolkit [filters](https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/filters.html), but we inherit from the custom `PythonInputFilter` defined in [ptpython.filters](https://github.com/prompt-toolkit/ptpython/blob/master/ptpython/filters.py#L13).


https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L191-L193

https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L204-L216

You can check [KosmosShell.py](https://github.com/threefoldtech/jumpscaleX_core/blob/development/JumpscaleCore/core/KosmosShell.py) to see where they're used.


## Updating layout
[ptpython](https://github.com/prompt-toolkit/ptpython) creates a [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/en/stable/) application, [and setup the layout](https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L204-L216), we get the main container of this layout and add our custom containers to it.

https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L219-L221

We use this container to setup e.g. logging pane as follows:

https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L251-L277

## Auto-completion
For auto-completion, we get the current typed line, remove trailing unecassarry characters, then due to the dynamic nature of jumpscale, we evaluate the line to get a function or a property object...etc, as static analysis does not always work, we do the same to get docstrings too.

We monkey patch `get_completions()` of [PythonCompleter](https://github.com/prompt-toolkit/ptpython/blob/master/ptpython/completer.py#L19) to be able to list certain members and classify them with colors:

https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L444-L466

The method yields [Completion](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/reference.html#module-prompt_toolkit.completion) instances with information from jumpscale object instead.



## Docstrings

We do the same as evaluation, except we only added a key binding of `?` for this operation.


https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L393-L419

## Exceptions and logging

`ptpython` implements a custom exception handler (as a hook), we just monkey-patch it to be able to format exception the same way we do in jumpscale:

https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L440

https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L160-L183

As you can see, original `_handle_exception()` can be found at [PythonRepl implementation](https://github.com/prompt-toolkit/ptpython/blob/master/ptpython/repl.py#L167).


For **Logging**, we just setup a pane and add logs to it, setting up the pane is done by `setup_logging_containers()` where we add a container that has `LogPane.Buffer` as buffer, with some [filters](#custom-filters) to show/hide it, also, we set jumpscale custom_log_printer to `add_logs_to_pane()` to intecept the logs and add it to the pane.

https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L469

https://github.com/threefoldtech/jumpscaleX_core/blob/d3b46156ac2f8f2724b3c78177930a2c4a22017a/JumpscaleCore/core/KosmosShell.py#L245-L248
