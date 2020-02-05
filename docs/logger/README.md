# Jumpscale Logger

## Logging mechanism

New jumpscale logger now stores logs in Redis up to 2K records then dumps the oldest 1K to filesystem
in `/sandbox/var/logs/<APP-NAME>`

To define app we use for example: `j.application.start("threebotserver")`

## Logger client

Gets logs for local/remote machine via redis

### How to use:

We can either use logger client or js_logs

#### Logger client
- Get a client for logger

```toml
@url = jumpscale.clients.logger.1
name** = ""
redis_addr = "127.0.0.1" (ipaddr)
redis_port = 6379 (ipport)
redis_secret = ""
"""
```

- Usage of client
```python
client = j.clients.logger.get("js_logs")
```

- Methods we use to list/print
```python
client.list(appname="test") # list all logs in testapp
client.print(appname="test") # print all logs (pretty format)
client.tail_get("test")  # get tail of latest logs
```

#### js_logs

- Get logs via shell

```bash
3BOTDEVEL:3bot:test: js_logs
Usage: js_logs [OPTIONS] COMMAND [ARGS]...

Options:
  -a, --appname TEXT    application name
  --redis-secret TEXT   redis secret (empty by default)
  --redis-port INTEGER  redis port (defaults to 6379)
  --redis-host TEXT     redis host (defaults to localhost)
  --help                Show this message and exit.

Commands:
  tail  tail logs from session
```

Example: `js_logs --appname test tail`

This will open a streaming tail with latest logs

## For References:

- Logger logic is implemented in `JSBASE` class `/sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/core/BASECLASSES/JSBase.py`

- Logger handlers are implemented in `InstallTools` at `LogHandler` class
