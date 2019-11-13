# 3Bot client

## Example on how to use the threebot client

- we need threebot server running and a package to test with

```python
cl = j.servers.threebot.local_start_default(web=True)
```

- Create the `default` instance from threebot.me

```python
cl.actors.package_manager.package_add(path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/phonebook")
cl.reload()
```

- At this point, no default `3bot me instance` configured, any attempt to call actor will not be authenticated i.e `user_session` will be empty

- Add 3bot me instance
```
j.tools.threebot.init_my_threebot(myidentity='default', name='hamdy farag', email='ham1dy@d.com', description=None, ipaddr='127.0.0.1', interactive=False)
```
- Add a test package and reload the server after loading the new package

```python
cl.actors.package_manager.package_add(path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/registry")
cl.reload()
```

- Get the client and use it (registering my threebot.me id), It will authenticate automatically

```python
c = j.clients.threebot.client_get(j.tools.threebot.me.default.tid)
```

- use the client

```python3
c.actors_default.registry.get(data_id=1)
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

- Other examples

```
client = j.clients.threebot.get(name='remote', host='172.17.0.5', port=8901)
client2.actors_default.html_test.hello_markdown()

## actors.default.html_test.hello.537cc19efef1a82cef8751bd84c39d82
 - content             : _markdown test_ Hello ``

```