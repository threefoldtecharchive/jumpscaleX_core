# Actors

- Actors are the logic inside packages that is also the implementation of our api for this package to the outside world, our interface basically. It can connect to clients/frontend.
- The code inside an actor should call as much as possible libraries in jumpscale (sals, clients, ...)
- Packages can have more than an actor.

## Actor Structure

- Actor is a python class file that inherits from `j.baseclasses.threebot_actor`

- Example actor
  
  ```python
  from Jumpscale import j
  
  class actor(j.baseclasses.threebot_actor):
  
      def test_method(self, tid=None, data_id=None, schema_out=None, user_session=None):
          """
          ```in
          tid = (I)
          data_id = (I)
          ```
  
          ```out
          res = !threebot.registry.entry.data.1
          ```
  
          ```auth
          public = False
          users = ["test1.3bot", "test2.3bot"]
          circles = ["testadmin.3bot", "testadmin2.3bot"]
          ```
          """
  
          # some logic here
          pass
  
  ```
  For more info check [Here](https://github.com/threefoldtech/jumpscaleX_threebot/blob/development/docs/quickstart.md)

- Methods docstring components

  - Schema in:

    ```python
        ```in
        tid = (I)
        data_id = (I)
        ```
    ```

  - Schema Out:

    ```python
        ```in
        tid = (I)
        data_id = (I)
        ```
    ```
  
  - Auth:

    Auth part is responsible for actor's security.
    determines if the actor's method is public or private.
    Also users and circles who have access to it
    for example:

  ```python
      ```auth
      public = False
      users = ["test1.3bot", "test2.3bot"]
      circles = ["testadmin.3bot", "testadmin2.3bot"]
      ```
  ```
  
  - By default methods only accessible by system admins `admin circle` and the default threebot me (No need to auth my self) which is defined by `BCDB ACLs`
  
  - If user has no access then it will search circles and subcircles. Check [here](https://github.com/threefoldtech/jumpscaleX_core/blob/development/JumpscaleCore/data/bcdb/models_system/ACL.md)

  - `users` containes the threebot names for authorized users.
  - `circles` containes the circles names for authorized circles.

  - If user is authorized (Has ACL rights) or in an authorized circle. then he can access the actor's method.
  
  ## Examples
  
  - Create some users
  
  ```python
  bcdb = j.data.bcdb.system
  ```

  ```python
  for i in range(10):
      u = bcdb.user.new()
      u.name = "ikke_%s" % i
      u.threebot_id = f"test{i}.3bot"
      u.email = "user%s@me.com" % i
      u.dm_id = "user%s.ibiza" % i
      u.save()
  ```
  
  - Create some circles
  
  ```python
  for i in range(10):
    g = bcdb.circle.new()
    g.name = "gr_%s" % i
    g.threebot_id = f"circle{i}.3bot"
    g.email = "circle%s@me.com" % i
    g.dm_id = "circle%s.ibiza" % i
    g.circle_members = [x for x in range(12, 14)]
    g.user_members = [x for x in range(1, i + 1)]
    g.save()
  ```
  
  - Create admin circle
  
  ```python
    g = bcdb.circle.new()
    g.name = "admins"
    g.threebot_id = f"admin.3bot"
    g.email = "admin@me.com"
    g.dm_id = "admin.ibiza"
    g.user_members = ["testadmin.3bot", "testadmin2.3bot"]
    g.save()
  ```
  
 - Add auth data to the actor.
 
 - Configure threebot.me tool
 
 ```python
 # Change the ip to the remote container
 j.tools.threebot.init_my_threebot(myidentity='test1.3bot', name='test1.3bot', email='user1@me.com', description=None, ipaddr='127.0.0.1', interactive=False)
```

 - Configure threebot client
 
 ```python
 # Change host with your remote container's ip
 client = j.clients.threebot.get(name='local', host='127.0.0.1', port=8901)
```

- Then use the actor using threebot client

```python
client.actors_default.alerta.new_alert(id=5) 
```