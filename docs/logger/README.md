# Jumpscale Logger

## Logging mechanism

New jumpscale logger now stores logs in Redis up to 2K records then dumps the oldest 1K to filesystem
in `/sandbox/var/logs/<APP-NAME>`

To define app we use for example: `j.application.start("threebotserver")` add this to your application init

## Logger client

Gets logs for local/remote machine via redis

### How to use:

We can either use logger client or js_logs

### Logger client

#### Get a client for logger

- Client params

```bash
name** = ""
redis_addr = "127.0.0.1" (ipaddr)
redis_port = 6379 (ipport)
redis_secret = ""
"""
```

- Client get

```python
client = j.clients.logger.get("js_logs")
```

### Usage of client

- list:  list all logs in testapp

    `client.list(appname="test")`

- tail: get tail of latest logs [as an api call]

    `client.tail_get("test") `

- find: find logs with a lot of filters (message, time, appname, cat, processid, filepath, .. )

    `client.find(appname="threebotserver", message=".md")`

- count: count logs if all=True will add the logs in filesystem too

    `client.count("threebotserver") `

- print: print & find logs (pretty format)

    `client.print(appname="test")`


### js_logs

#### Get logs via shell

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

Examples:

- `js_logs --appname test tail`: This will open a streaming tail with latest logs

- `js_logs -a threebotserver find --message "connection error"`: This will search all logs for message with message connection error
    - other filters for find:

         ```bash
          --file_path TEXT  filter by logsfilepath logs come from , defaults to None
          --level TEXT      filter by log level , defaults to None
          --data TEXT       filter by log data , defaults to None
          --cat TEXT        filter by category, defaults to empty string
          --message TEXT    filter by string
          --processid TEXT  filter by process id, defaults to None
          --time_from TEXT  filter by time within a span from specific time, defaults
                            to None
          --time_to TEXT    filter by time within a span until specific time ,
                            defaults to None
          --id_from TEXT    filter by logs id from , defaults to None
        ```

- `js_logs -a threebotserver count all=True`: will show logs count, if all=True will also count logs in filesystem

## For References:

- Logger logic is implemented in `JSBASE` class `/sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/core/BASECLASSES/JSBase.py`

- Logger handlers are implemented in `InstallTools` at `LogHandler` class
