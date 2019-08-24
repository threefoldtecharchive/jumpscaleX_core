# use log handler to filesystem

it uses the log handler function of jumpscale

## video

see [https://vimeo.com/353947167](https://vimeo.com/353947167)

## example method to register the log handler and set the session

```python

#check the session has already been set, if not set 
if not j.application._log2fs_session_name:
    j.application.log2fs_register(builder._name)

#do this for each step where you want to start a new file for the logging 
j.application.log2fs_context_change(name)

```