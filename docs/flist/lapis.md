## Lapis Flist

The lapis builder exposes a funcationality to create a lapis flist that autostarts lapis on container creation.
The autostart script creates a lapis project under `/lapis_project` on the container and starts lapis using the default configuration.

To build the flist and upload it to the hub, simply run the following command where hub is the name of the zhub client instance on your system.

```python
j.builders.web.lapis.flist_create(hub)
```

Alternatively, you can use the [lapis flist](https://hub.grid.tf/tf-official-apps/lapis.flist) from our official apps, to create a container that will autostart openresty.

```
 client.container.create('https://hub.grid.tf/tf-official-apps/lapis.flist', env={
          'LD_LIBRARY_PATH':'/sandbox/lib/',
          'LUALIB': '/sandbox/openresty/lualib',
          'LUA_PATH': '?.lua;/sandbox/openresty/lualib/?/init.lua;/sandbox/openresty/lualib/?.lua;/sandbox/openresty/lualib/?/?.lua;/sandbox/openresty/lualib/?/core.lua;/sandbox/openresty/lapis/?.lua',
          'LUA_CPATH': '/sandbox/openresty/lualib/?.so;./?.so',
          'LAPIS_OPENRESTY': '/sandbox/bin/openresty',
          'PBASE': '/sandbox',
          'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/sandbox/bin'})
```

After container creation, you'll find the job `lapisserver` running on the container. This is the lapis serrver process and it uses the configuration located at `/lapis_project/nginx.conf`. Lapis will be listening on port `8080`.



