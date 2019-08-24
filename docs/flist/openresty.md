## OpenResty Flist

The openresty builder exposes a funcationality to create an openresty flist that autostarts openresty on container creation.
To build the flist and upload it to the hub, simply run the following command where hub is the name of the zhub client instance on your system.

```python
j.builders.web.openresty.flist_create(hub)
```

Alternatively, you can use the [openresty flist](https://hub.grid.tf/tf-official-apps/openresty.flist) from our official apps, to create a container that will autostart openresty.

```
 client.container.create('https://hub.grid.tf/tf-official-apps/openresty.flist', env={
          'LD_LIBRARY_PATH':'/sandbox/lib/',
          'LUALIB': '/sandbox/openresty/lualib',
          'LUA_PATH': '?.lua;/sandbox/openresty/lualib/?/init.lua;/sandbox/openresty/lualib/?.lua;/sandbox/openresty/lualib/?/?.lua;/sandbox/openresty/lualib/?/core.lua;/sandbox/openresty/lapis/?.lua',
          'LUA_CPATH': '/sandbox/openresty/lualib/?.so;./?.so',
          'LAPIS_OPENRESTY': '/sandbox/bin/openresty'})
```

After container creation, you'll find the job `openresty` running on the container. This is the openresty process and it uses the configuration located at `/sandbox/cfg/openresty.cfg`. Openresty will be listening on port `8081`.



