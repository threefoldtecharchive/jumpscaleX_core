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

```python
    @repl.add_key_binding(Keys.ControlJ)
    def _debug_event(event):
        """
        custom binding for pudb, to allow debugging a statement and also
        post-mortem debugging in case of any exception
        """
        b = event.cli.current_buffer
        app = get_app()
        statements = b.document.text
        if statements:
            import linecache


            linecache.cache["<string>"] = (len(statements), time.time(), statements.split("\n"), "<string>")
            app.exit(pudb.runstatement(statements))
            app.pre_run_callables.append(b.reset)
        else:
            pudb.pm()
```

See [more about prompt-toolit key bindings](https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/key_bindings.html).


## Custom filters
We define some custom fitlers that we use inside layouts and key bindings, filters are just prompt-toolkit [filters](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/advanced_topics/filters.html), but we inherit from the custom `PythonInputFilter` defined in [ptpython.filters](https://github.com/prompt-toolkit/ptpython/blob/master/ptpython/filters.py#L13).


```python
class HasDocString(PythonInputFilter):
    def __call__(self):
        return len(self.python_input.docstring_buffer.text) > 0
```

```python
class HasLogs(PythonInputFilter):
    def __call__(self):
        j = KosmosShellConfig.j
        panel_enabled = bool(j.core.myenv.config.get("LOGGER_PANEL_NRLINES"))
        in_autocomplete = j.application._in_autocomplete
        return LogPane.Show and panel_enabled and not in_autocomplete




class IsInsideString(PythonInputFilter):
    def __call__(self):
        text = self.python_input.default_buffer.document.text_before_cursor
        grammer = self.python_input._completer._path_completer_grammar
        return bool(grammer.match(text))
```

You can check [KosmosShell.py](https://github.com/threefoldtech/jumpscaleX_core/blob/development/JumpscaleCore/core/KosmosShell.py) to see where they're used.


## Updating layout
[ptpython](https://github.com/prompt-toolkit/ptpython) creates a [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/en/stable/) application, [and setup the layout](https://github.com/prompt-toolkit/ptpython/blob/master/ptpython/layout.py#L495), we get the main container of this layout and add our custom containers to it.

```python
def get_ptpython_parent_container(repl):
    # see ptpython.layout
    return repl.app.layout.container.children[0].children[0]
```

We use this container to setup e.g. logging pane as follows:

```python
def setup_logging_containers(repl):
    j = KosmosShellConfig.j


    panel_line_count = j.core.myenv.config.get("LOGGER_PANEL_NRLINES", 12)
    parent_container = get_ptpython_parent_container(repl)
    parent_container.children.extend(
        [
            ConditionalContainer(
                content=Window(height=Dimension.exact(1), char="\u2500", style="class:separator"),
                filter=HasLogs(repl) & ~is_done,
            ),
            ConditionalContainer(
                content=Window(
                    BufferControl(
                        buffer=LogPane.Buffer,
                        input_processors=[FormatANSIText(), HighlightIncrementalSearchProcessor()],
                        focusable=False,
                        preview_search=True,
                    ),
                    wrap_lines=True,
                    height=Dimension.exact(panel_line_count),
                ),
                filter=HasLogs(repl) & ~is_done,
            ),
        ]
    )
```

## Auto-completion
For auto-completion, we get the current typed line, remove trailing unecassarry characters, then due to the dynamic nature of jumpscale, we evaluate the line to get a function or a property object...etc, as static analysis does not always work, we do the same to get docstrings too.

We monkey patch `get_completions()` of [PythonCompleter](https://github.com/prompt-toolkit/ptpython/blob/master/ptpython/completer.py#L19) to be able to list certain members and classify them with colors:

```python
    old_get_completions = repl._completer.__class__.get_completions


    def custom_get_completions(self, document, complete_event):
        j.application._in_autocomplete = True


        try:
            _, _, prefix = get_current_line(document)
        except ValueError:
            return


        completions = []
        try:
            completions = list(get_completions(self, document, complete_event))
        except Exception:
            j.tools.logger._log_error("Error while getting completions\n" + traceback.format_exc())


        # j.tools.logger._log_error(completions)


        if not completions:
            completions = old_get_completions(self, document, complete_event)


        j.application._in_autocomplete = False
        yield from filter_completions_on_prefix(completions, prefix)
```

The method yields [Completion](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/reference.html#module-prompt_toolkit.completion) instances with information from jumpscale object instead.



## Docstrings

We do the same as evaluation, except we only added a key binding of `?` for this operation.

```python
    @repl.add_key_binding("?", filter=~IsInsideString(repl))
    def _docevent(event):
        b = event.cli.current_buffer
        parent, member, _ = get_current_line(b.document)
        member = member.rstrip("(")


        try:
            d = None
            try:
                # try get the class member itself first
                d = get_doc_string(f"{parent}.__class__.{member}", repl.get_locals(), repl.get_globals())
            except:
                pass


            if not d:
                if parent:
                    d = get_doc_string(f"{parent}.{member}", repl.get_locals(), repl.get_globals())
                else:
                    d = get_doc_string(member, repl.get_locals(), repl.get_globals())
        except Exception as exc:
            j.tools.logger._log_error(str(exc))
            repl.docstring_buffer.reset()
            return


        if d:
            repl.docstring_buffer.reset(document=Document(d, cursor_position=0))

```

## Exceptions and logging

`ptpython` implements a custom exception handler (as a hook), we just monkey-patch it to be able to format exception the same way we do in jumpscale:

```python
    repl._handle_exception = partial(patched_handle_exception, repl)
```


```python
def patched_handle_exception(self, e):
    j = KosmosShellConfig.j


    # Instead of just calling ``traceback.format_exc``, we take the
    # traceback and skip the bottom calls of this framework.
    t, v, tb = sys.exc_info()


    output = self.app.output
    # Required for pdb.post_mortem() to work.
    sys.last_type, sys.last_value, sys.last_traceback = t, v, tb


    # loop until getting actual traceback (without internal ptpython part)
    last_stdin_tb = tb
    while tb:
        if tb.tb_frame.f_code.co_filename == "<stdin>":
            last_stdin_tb = tb
        tb = tb.tb_next


    logdict = j.core.tools.log(tb=last_stdin_tb, level=50, exception=e, stdout=False)
    formatted_tb = j.core.tools.log2str(logdict, data_show=True, replace=True)
    print_formatted_text(ANSI(formatted_tb))


    output.write("%s\n" % e)
    output.flush()
```

As you can see, original `_handle_exception()` can be found at [PythonRepl implementation](https://github.com/prompt-toolkit/ptpython/blob/master/ptpython/repl.py#L167).


For **Logging**, we just setup a pane and add logs to it, setting up the pane is done by `setup_logging_containers()` where we add a container that has `LogPane.Buffer` as buffer, with some [filters](#custom-filters) to show/hide it, also, we set jumpscale custom_log_printer to `add_logs_to_pane()` to intecept the logs and add it to the pane.

```python
    j.core.tools.custom_log_printer = add_logs_to_pane
```

```python
def add_logs_to_pane(msg):
    LogPane.Buffer.insert_text(data=msg, fire_event=False)
    LogPane.Buffer.newline()
    LogPane.Buffer.auto_down(count=LogPane.Buffer.document.line_count)
```
