# running
```
 kosmos 'j.servers.gundb._server_test_start()'
```

### usage with bcdb

assuming you have these schemas registered in your system

```
bcdb = j.data.bcdb.get(name="test")
bcdb.reset()
j.data.schema.get_from_text("""
@url = proj.todo
title* = "" (S)
done* = False (B)

""")

j.data.schema.get_from_text("""
@url = proj.todolist
name* = "" (S)
todos* = (LO) !proj.todo

""")
j.data.schema.get_from_text("""
@url = proj.simple
attr1* = "" (S)
attr2* = 0 (I)
mychars* = (LS) 
""")

j.data.schema.get_from_text("""
@url = proj.email
addr* = "" (S)
""")
j.data.schema.get_from_text("""
@url = proj.person
name* = "" (S)
email* = "" !proj.email
""")


j.data.schema.get_from_text("""
@url = proj.os
name* = "" (S)
""")


j.data.schema.get_from_text("""
@url = proj.phone
model* = "" (S)
os* = "" !proj.os
""")


j.data.schema.get_from_text("""
@url = proj.human
name* = "" (S)
phone* = "" !proj.phone
""")


```
you can use them from your javascript code using `gun.js` client

```javascript
    <script src="https://cdn.jsdelivr.net/npm/gun/gun.js"></script>

      var gun = Gun("ws://172.17.0.2:7766/gun")

      gun.get("proj.human://1").put({"name":"xmon"})
      gun.get("proj.human://1").get("phone").put({
          "model":"samsung"
      })
      gun.get("proj.human://1").get("phone").get("os").put({
          "name":"android"
      })

      gun.get("proj.human://2").put({"name":"richxmon"})
      gun.get("proj.human://2").get("phone").put({
          "model":"iphone"
      })
      gun.get("proj.human://2").get("phone").get("os").put({
          "name":"ios"
      })
```

in the server output logs you see something like

```
success.....!!!!! id = 1
name = "xmon"
phone = "{'model': 'samsung', 'os': {'name': 'android'}}"

success.....!!!!! id = 2
name = "richxmon"
phone = "{'model': 'iphone', 'os': {'name': 'ios'}}"

```


there're some test scripts in html directory make sure to update the gun server endpoint



## Difference from reference gun.js usage

We use Gun.js javascript client to communicate with pygundb as normal, but with some conventions

1- we work against root objects that has some schema encoding `proj.simple` for instance in the server side we use this information for object retrieval and attributes validation
2- we use root object ids `SCHEMA://ID` to retrieve the object
3- simple attributes can be updated using `put`

```javascript
      var gun = Gun("ws://127.0.0.1:8000/gun")

      let basicTest = () => {
        gun.get("proj.simple://1").put({
          "attr1": "val"
        })
        gun.get("proj.simple://2").put({
          "attr2": 5
        })

      }
```

4- for nested objects we use `.get` to work on a nested object
```javascript

      let midTest = () => {

        gun.get("proj.person://4").put({
          name: "ahmed"
        })
        gun.get("proj.person://4").put({
          "name": "ahmed"
        })
        gun.get("proj.person://4").get("email").put({
          "addr": "ahmed@gmail.com",
        })
        gun.get("proj.person://5").get("email").put({
          "addr": "andrew@gmail.com",
        })
        gun.get("proj.person://5").get("email").put({
          "addr": "dmdm@gmail.com",
        })
        gun.get("proj.person://5").get("email").put({
          "addr": "notdmdm@gmail.com",
        })

      }
```

5- working with sets of objects you need to declare they're a list using `list_` prefix for the property name

```javascript

      let advTest = () => {

        gun.get("proj.human://7").put({
          "name": "xmon"
        })
        gun.get("proj.human://7").get("phone").put({
          "model": "samsung"
        })
        gun.get("proj.human://7").get("phone").get("os").put({
          "name": "android"
        })

        gun.get("proj.human://8").put({
          "name": "richxmon"
        })
        gun.get("proj.human://8").get("phone").put({
          "model": "iphone"
        })
        gun.get("proj.human://8").get("phone").get("os").put({
          "name": "ios"
        })
        gun.get("proj.human://8").get("list_favcolors").set("white")
        gun.get("proj.human://8").get("list_favcolors").set("red")
        gun.get("proj.human://8").get("list_favcolors").set("blue")

        gun.get("proj.human://8").get("list_langs").set({
          "name": "python"
        })
        gun.get("proj.human://8").get("list_langs").set({
          "name": "ruby"
        })
```


