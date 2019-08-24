
## js_init

```bash
Usage: js_init [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  fix       fix broken files, best to do a scan first so...
  generate  generate the loader file, important to do...
  scan      find files which can be fixed and print
```

when jumpscale env is out of sync, you can generate the loader files with 

js_init generate

### to fix code 

first do

```
js_init scan
```

output will be something like

```bash
[##### line change [3]

- /Users/despiegk/code/github/threefoldtech/0-robot/JumpscaleZrobot/clients/zerorobot/ZeroRobotFactory.py
- line old : 'from jumpscale import j'
- line new : 'from Jumpscale import j'
, ##### line change [8]

- /Users/despiegk/code/github/threefoldtech/0-robot/JumpscaleZrobot/clients/zerorobot/ZeroRobotFactory.py
- line old : 'JSConfigFactoryBase = j.tools.configmanager.base_class_configs'
- line new : 'JSConfigFactoryBase = j.application.JSFactoryBaseClass'
, ##### line change [2]

- /Users/despiegk/code/github/threefoldtech/0-robot/JumpscaleZrobot/clients/zerorobot/ZeroRobotClient.py
- line old : 'from jumpscale import j'
- line new : 'from Jumpscale import j'
, ##### line change [6]

- /Users/despiegk/code/github/threefoldtech/0-robot/JumpscaleZrobot/clients/zerorobot/ZeroRobotClient.py
- line old : 'JSConfigClientBase = j.tools.configmanager.base_class_config'
- line new : 'JSConfigClientBase = j.baseclasses.object'
, ##### line change [2]

- /Users/despiegk/code/github/threefoldtech/0-robot/JumpscaleZrobot/servers/zerorobot/ZeroRobotServer.py
- line old : 'from jumpscale import j'
- line new : 'from Jumpscale import j'
, ##### line change [23]

- /Users/despiegk/code/github/threefoldtech/0-robot/JumpscaleZrobot/servers/zerorobot/ZeroRobotServer.py
- line old : 'JSConfigBase = j.tools.configmanager.base_class_config'
- line new : 'JSConfigBase = j.baseclasses.object'
, ##### line change [0]

- /Users/despiegk/code/github/threefoldtech/0-robot/JumpscaleZrobot/servers/zerorobot/ZeroRobotFactory.py
- line old : 'from jumpscale import j'
- line new : 'from Jumpscale import j'
, ##### line change [4]

- /Users/despiegk/code/github/threefoldtech/0-robot/JumpscaleZrobot/servers/zerorobot/ZeroRobotFactory.py
- line old : 'JSConfigBase = j.tools.configmanager.base_class_configs'
- line new : 'JSConfigBase = j.application.JSFactoryBaseClass'
]
```

if you like the suggested changes do

js_init fix

now the files will be rewritten
