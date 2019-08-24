###  Configuring OpenPublish

OpenPublish tool uses JSX config manager to save its configurations.

You will need to configure it through kosmos shell as following:

```python
j.servers.threebot.get(name="default")
```

Here is the output:
```
- name                          : default
- websites                      : []
- wikis                         : []
- zdb                           :
    ## jumpscale.open_publish.zdb.1
    id: None name:'main'
    - adminsecret_                  : password
    - host                          : 127.0.0.1
    - mode                          : seq
    - name                          : main
    - port                          : 9,900

- gedis                         :
    ## jumpscale.open_publish.gedis.1
    id: None name:'main'
    - host                          : 0.0.0.0
    - name                          : main
    - password_                     :
    - port                          : 8,888
    - ssl                           : False
```

- name: The name of the tool we only used the name `default` to be able to refer to it from gedis actors
- websites: list of websites published by the tool. Each website schema contains name, domain, repo.
- wikis: list of wikis published by the tool. Each wiki schema contains name, domain, repo.

- zdb: the configs related to zdb server which will be started by open publish tool. You can change its configs
(i.e. adminsecret_) from kosmos shell as following:

```python
open_publish_tool = j.servers.threebot.get(name="default")
open_publish_tool.zdb.adminsecret_ = "New Password"
open_publish_tool.save()
```

- gedis: the configs related to gedis server which will be started by open publish tool. You can change its configs
(i.e. port) from kosmos shell as following:

```python
open_publish_tool = j.servers.threebot.get(name="default")
open_publish_tool.gedis.port = 8888
open_publish_tool.save()
```
Note that if you changed the gedis default port (8888) you will need to update [OpenPublish](https://github.com/threefoldtech/OpenPublish) config file.
