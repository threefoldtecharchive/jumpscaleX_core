# 3Bot client

## Example on how to use the threebot client

- we need threebot server running and a package to test with

```python
cl = j.servers.threebot.local_start_default(web=True)
```

- Add a test package and reload the server after loading the new package

```python
cl.actors.package_manager.package_add(path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/registry")
cl.reload()
```

- Get/Create the `default` instance from threebot.me

```python
client = j.tools.threebot.me.get("default", tid=1, email="test@test.com", tname="first")
```

- Register threebot.me instance to the phonebook

```python
nacl = client.nacl
pubkey = nacl.verify_key_hex
client.pubkey=pubkey
tid = client.tid
name = client.name
email = client.email
ipaddr = ""
description = ""
sender_signature_hex = j.data.nacl.payload_sign(tid, name, email, ipaddr, description, pubkey, nacl=nacl)
# Register to phonebook
name_for_register = cl.actors.phonebook.name_register(name="default", pubkey=pubkey)
name_for_register.signature = sender_signature_hex
name_for_register.email = email
name_for_register.id = tid
```

- Add the threebot.me record to phonebook

```python
cl.actors.phonebook.record_register(
    tid=tid, name=name, email=email, description=description, pubkey=pubkey, sender_signature_hex=sender_signature_hex
)
```

- Get the client and use it (registering my threebot.me id), It will authenticate automatically

```python
c = j.clients.threebot.client_get(threebot=1)
c.host = "127.0.0.1"
c.save()
```

- use the client

```python3
c.actors_default.registry.get(data_id=2)
```

Here we can see user_session is filled with the threebot client info

```python
## session Session


### properties:
 - admin                : False
 - content_type         : AUTO
 - kwargs               : []
 - response_type        : AUTO
 - threebot_circles     : []
 - threebot_client      : ## .threebot.client
 - threebot_id          : 1
 - threebot_name        : default
```
