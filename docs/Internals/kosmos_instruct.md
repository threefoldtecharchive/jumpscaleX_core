
## config file for kosmos

jumpscale has ability to call any command in jumpscale by means of an instruction toml file.
This is a good way how to do something automated e.g. during an automated install.

```python
j.data.nacl.configure(name='default', privkey_words=None, secret=None, sshagent_use=None, interactive=False, generate=False)
```

can be called as follows

```toml
[[instruction]]
instruction_method = "j.data.nacl.configure"
instruction_name= "optional_name"
instruction_description = "does not have to be used"
name = "default"
sshagent_use = true
generate = true
```

call with

kosmos --instruct="/tmp/myconfig.toml"

only specify the arguments you need for the other the default values will be used.


ofcourse you can specify this multiple times as follows

```toml

[[instruction]]
instruction_method = "j.data.nacl.configure"
name = "default"
sshagent_use = true
generate = true

[[instruction]]
instruction_method = "j.data.nacl.configure"
name = "something"
sshagent_use = true
generate = true

[[instruction]]
instruction_method = "j.tools.console.echo"
msg = "this message will be send to screen"

[[instruction]]
instruction_method = "j.tools.console.echo"
msg = "this message will be send to screen"

```

## shortcut way

There is a shortcut way (more dense), but order cannot be guaranteed

```toml

[["j.data.nacl.configure"]]
name = "default"
sshagent_use = true
generate = true

[["j.data.nacl.configure"]]
name = "something"
sshagent_use = true
generate = true


[["j.tools.console.echo"]]
msg = "this message will be send to screen"

```

only works when starting with j. and needs to be in double '"'

will return the output and at the end will print 

```
####TOMLRESULT####
... the result in toml format
```


## combine with debugging or ignore errors

```bash
kosmos --instruct="/tmp/myconfig.toml" --debug
```

will call the debugger when there is an issue, super easy to debug.

```bash
kosmos --instruct="/tmp/myconfig.toml" --ignore_error
```

will ignore errors and do all the instructions even if errors happen

## can be used for defining test cases

just create a toml instruction file & execute with one of relevant options

## Example

```python
Sat16 12:36 SystemFS.py      - 120 - j.sal.fs:systemfs                  : path /sandbox/cfg/nacl/something is not a link
Sat16 12:36 SystemFS.py      - 972 - j.sal.fs:systemfs                  : path /sandbox/cfg/nacl/something is not a link
Sat16 12:36 NACL.py          - 145 - j.sal.fs:systemfs                  : Directory trying to create: [/sandbox/cfg/nacl/something] already exists
Sat16 12:36 SystemFS.py      - 878 - j.sal.fs:systemfs                  : path b'/sandbox/var/logs/myprocess_something.log' does not exist
Sat16 12:36 SystemProcess.py -  69 - execute                            : execute:ssh-add -L
Sat16 12:36 SystemProcess.py -  69 - execute                            : execute:ssh-add -L
Sat16 12:36 NACL.py          - 371 - j.sal.fs:systemfs                  : Read file: /sandbox/cfg/nacl/something/key.priv
* instruction run:
          description: ''
          error: false
          kwargs:
              msg: this message will be send to screen
          method: j.tools.console.echo
          name: ''
this message will be send to screen
* instruction run:
          description: ''
          error: false
          kwargs:
              msg: this message will be send to screen
          method: j.tools.console.echo
          name: ''
this message will be send to screen


####TOMLRESULT####


[[instruction]]
description = ""
error = false
method = "j.data.nacl.configure"
name = ""
result = "COULDNOTSERIALIZE"

[instruction.kwargs]
generate = true
name = "default"
sshagent_use = true

[[instruction]]
description = ""
error = false
method = "j.data.nacl.configure"
name = ""
result = "COULDNOTSERIALIZE"

[instruction.kwargs]
generate = true
name = "something"
sshagent_use = true

[[instruction]]
description = ""
error = false
method = "j.tools.console.echo"
name = ""
result = "null"

[instruction.kwargs]
msg = "this message will be send to screen"

[[instruction]]
description = ""
error = false
method = "j.tools.console.echo"
name = ""
result = "null"

[instruction.kwargs]
msg = "this message will be send to screen"

```


