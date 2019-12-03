


### Threebot will start the following servers by default

- zdb                                         (port:9900)
- sonic                                       (port:1491)
- gedis                                       (port:8901)
- bcdb redis interface                        (port:6380)

```
if web:
    openresty                                                   (port:80 and 443 for ssl)
    on the gevent loop:
        gedis websocket                                         (port:8902)  #used for search in wiki
        bottle server for webinterface (gedis to http)          (port:8903)
        bottle server for bcdfs (filemanager)                   (port:8904) serves the bcdbfs content
    map on openresty: on port 80 and 443
        $addr/web/gedis/http_websocket
        $addr/web/gedis/http
        $addr/api/filemanager
```
