# Jumpscale Alerts

## alerts client

Jumpscale alerts stores alerts in Redis so we can get local/remote alerts through it

## Usage:

### Get alerts client

- params
    ```bash
    redis_addr = "127.0.0.1" (ipaddr)
    redis_port = 6379 (ipport)
    redis_secret = ""
    ```

- Get a client

    ```python
    client = j.clients.alerts.get("js_alerts")
    ```

### Usage of the client

- `client.list()`: list all alerts

- `client.find(message="no")` : find alerts by message, time, cat

## js_alerts

- via js shell

```bash
3BOTDEVEL:3bot:test: js_alerts
Usage: js_alerts [OPTIONS] COMMAND [ARGS]...

Options:
  --redis-secret TEXT   redis secret (empty by default)
  --redis-port INTEGER  redis port (defaults to 6379)
  --redis-host TEXT     redis host (defaults to localhost)
  --help                Show this message and exit.

Commands:
  count   print count of alerts
  delete  delete alert with given identifier
  find    filter by category, message, pid and/or time
  list    print all alerts
  reset   erase the alerts in the DB
  show    show alert with given identifier
```

### Examples

- Count alerts

```bash
3BOTDEVEL:3bot:test: js_alerts count
Count of alerts is 3
```

- List all alerts

```bash
js_alerts list
```

- Find alerts

```bash
js_alerts find --time 1580989035
```

### References:

- AlertHandlers: you can find at: `/sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/tools/alerthandler/RedisAlertHandler.py`

- js_alerts: `sandbox/code/github/threefoldtech/jumpscaleX_core/cmds/js_alerts`
