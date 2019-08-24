# Logging

```python

#in each JSBase class

self._log(...)
self._log_debug(...)

```


## how to add you're own log handling

register a handler to the ```j.application.loghandlers```

```python
def loghandler(logdict):
    #do something with the logdict
j.application.log_handlers.append(loghandler)
```

see [logdict](logdict.md) for format info
We use the logdict as generic format for the log handling.

Example usecases escalate to a remote controller or store in a DB or create alerts...

