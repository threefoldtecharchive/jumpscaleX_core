# profile management

there are 3 profiles in the builders

- home
- building 
- sandbox, is the default one

## how to select a profile

- profile_home_select()  
- profile_sandbox_select() #is the default
- profile_builder_select()

## default profile for building is

```python
self._remove("{DIR_BUILD}/env.sh")
self._bash = j.tools.bash.get(self._replace("{DIR_BUILD}"))

self.profile.env_set("PYTHONHTTPSVERIFY",0)
self.profile.env_set("PYTHONHOME",self._replace("{DIR_BUILD}"))

self.profile.env_set_part("LIBRARY_PATH","/usr/lib")
self.profile.env_set_part("LIBRARY_PATH","/usr/local/lib")
self.profile.env_set_part("LIBRARY_PATH","/lib")
self.profile.env_set_part("LIBRARY_PATH","/lib/x86_64-linux-gnu")
self.profile.env_set_part("LIBRARY_PATH","$LIBRARY_PATH",end=True)

self.profile.env_set("LD_LIBRARY_PATH",self.profile.env_get("LIBRARY_PATH")) #makes copy
self.profile.env_set("LDFLAGS","-L'%s'"%self.profile.env_get("LIBRARY_PATH"))

self.profile.env_set("LC_ALL","en_US.UTF-8")
self.profile.env_set("LANG","en_US.UTF-8")
self.profile.env_set("PS1","PYTHONBUILDENV: ")

self.profile.env_set_part("CPPPATH","/usr/include")
self.profile.env_set("CPATH",self.profile.env_get("CPPPATH"))
self.profile.env_set("CPPFLAGS","-I'%s'"%self.profile.env_get("CPPPATH"))

self.profile.path_add("${PATH}",end=True)
```

## how to select & add info to the builder profile

implement: profile_builder_set

```python

def profile_builder_set(self):

    self._log_info("build profile builder")

    self.profile.path_add(self._replace("{PATH_OPENSSL}"))

    self.profile.env_set("PYTHONHTTPSVERIFY",0)
    self.profile.env_set("PYTHONHOME",self._replace("{DIR_BUILD}"))

    self.profile.env_set_part("LIBRARY_PATH",self._replace("{PATH_OPENSSL}/lib"))

    self.profile.env_set_part("CPPPATH",self._replace("{DIR_BUILD}/include/python3.7m"))
    self.profile.env_set_part("CPPPATH",self._replace("{PATH_OPENSSL}/include"))

```

when you need the profile builder to be active do

- profile_builder_select()

## how to select & add info to the sandbox profile

implement: profile_sandbox_set

```python

def profile_sandbox_set(self):
    self.profile.env_set("SOME","aaa")

```

when you need the profile sandbox to be active do

- profile_sandbox_select()

## default profile for sandbox is

```python
self._bash = j.tools.bash.get("/sandbox/env.sh")

self.profile.path_add("/sandbox/bin")

self.profile.env_set("PYTHONHTTPSVERIFY",0)
self.profile.env_set("PYTHONHOME","/sandbox")

self.profile.env_set_part("PYTHONPATH","/sandbox/lib/python.zip")
self.profile.env_set_part("PYTHONPATH","/sandbox/lib")
self.profile.env_set_part("PYTHONPATH","/sandbox/lib/python3.7")
self.profile.env_set_part("PYTHONPATH","/sandbox/lib/python3.7/site-packages")
self.profile.env_set_part("PYTHONPATH","sandbox/lib/python3.7/lib-dynload")
self.profile.env_set_part("PYTHONPATH","/sandbox/bin")

self.profile.env_set_part("LIBRARY_PATH","/sandbox/bin")
self.profile.env_set_part("LIBRARY_PATH","/sandbox/lib")
self.profile.env_set("LD_LIBRARY_PATH",self.profile.env_get("LIBRARY_PATH")) #makes copy

self.profile.env_set("LDFLAGS","-L'%s'"%self.profile.env_get("LIBRARY_PATH"))

self.profile.env_set("LC_ALL","en_US.UTF-8")
self.profile.env_set("LANG","en_US.UTF-8")
self.profile.env_set("PS1","JSX: ")

self.profile.path_delete("${PATH}")

if j.core.platformtype.myplatform.platform_is_osx:
    self.profile.path_add("${PATH}",end=True)
```
