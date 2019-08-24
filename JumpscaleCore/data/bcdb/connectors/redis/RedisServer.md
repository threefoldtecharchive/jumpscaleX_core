# Redis Server


## HGET

### schemas:mid $SID

sid is the schema id

### schemas:url $URL

### schemas:hash $MD%

### schemas:url2sid $url

will return the sid

### schemas:url2hash $url

will return the hash of the schema

### data:$nid:sid:$sid $object_id

### data:$nid:url:$url $object_id

### data:$nid:hash:$hash $object_id


## HSET

same as HGET but now put info in
for schema is the text+url
for data is the json

## others

will need the HSCAN, HLEN, HDEL, ...

## COMMANDS

### FORMAT "JSON" / "YAML" / "TOML"

can call this command and it will influence the way how data is returned or given to the redis server



# tips

```bash
kosmos 'j.data.bcdb.redis_server_start(ipaddr="localhost", name="test", port=6380, secret="123456", bcdbname="test", )'
```
