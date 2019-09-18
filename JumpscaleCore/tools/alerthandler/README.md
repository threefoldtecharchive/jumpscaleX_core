# Alert Handler
Alert handler tool to create alerts from errors logged by jumpscale [error handler](../../../docs/Internals/logging_errorhandling/README.md).


## Usage

### Setup

You must setup alert handler first

```python
j.tools.alerthandler.setup()
```

### Listing alerts

Using bcdb:

```python
j.tools.alerthandler.model.find()
```
