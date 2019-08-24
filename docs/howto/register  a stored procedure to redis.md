# How to register a stored procedure to redis using redis client
First please read this [introduction to eval](https://redis.io/commands/eval#introduction-to-eval) to understand how 
eval and evalsha work

## Register a procedure from path
you can register a procedure from a lua script path like this
```python
redis_client.storedprocedure_register(name="test", nrkeys=3, path="path_to_lua_script")
```
will return the sha

the stored procedure can be found in hset `storedprocedures:$name` has inside a json with
 - script: the lua script
 - sha: the sha which van be used later to execute the procedure
 - nrkeys: number of keys that your script require

there is also another hset `storedprocedures_sha` that contains shas directly, use this if you know the name and what 
evalsha directly without parsing json


## use the registered procedure

1- if you are using jumpscale redis client:  
    you can use evalsha to execute the procedure if you know the sha like this
```python
redisclient.evalsha(sha,3,"a","b","c")  3 is for nr of keys, then the args
```
or you can directly execute it with name like this
```python
redisclient.storedprocedure_execute(name, *args)
```

2- if you are using the standard redis client:
in this case you will have to use evalsha command 
```
redis_cli> evalsha $sha $nr_keys $keys
```