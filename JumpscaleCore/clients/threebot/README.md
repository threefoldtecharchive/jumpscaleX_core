## 3 Bot client 

### Example on how to use the client
```
cl = j.servers.threebot.local_start_default(web=True)
cl.actors.package_manager.package_add(path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/registry")
cl.reload()



client = j.tools.threebot.me.get("default", tid=1, email="test@test.com", tname="first")
nacl = client.nacl
pubkey = nacl.verify_key_hex
client.pubkey=pubkey
tid = client.tid
name = client.name
email = client.email
ipaddr = ""
description = ""
sender_signature_hex = j.data.nacl.payload_sign(tid, name, email, ipaddr, description, pubkey, nacl=nacl)

name_for_register = cl.actors.phonebook.name_register(name="default", pubkey=pubkey)
name_for_register.signature = sender_signature_hex
name_for_register.email = email
name_for_register.id = tid


seed = client.nacl.words
signature = client.nacl.sign(client.nacl.words)

cl.actors.phonebook.record_register(
    tid=tid, name=name, email=email, description=description, pubkey=pubkey, sender_signature_hex=sender_signature_hex
)

c = j.clients.threebot.client_get(threebot=1)
c.host = "127.0.0.1"
c.save()

# Authenticate

c.auth(1)
c.actors_default.registry.schema_register() 
```

