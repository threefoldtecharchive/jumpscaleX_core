from Jumpscale import j


def main(self):
    """
    kosmos -p 'j.servers.openresty.test(name="tcp_proxy")'
    kosmos 'j.servers.openresty.test(name="tcp_proxy")'
    :return:
    """

    # start echo websocket proxy server
    cmd = """
from Jumpscale import j
rack = j.servers.rack.get()
rack.websocket_server_add("test", port=4444)
rack.start()  
"""
    s = j.servers.startupcmd.get(
        name="websocket_test_server", cmd_start=cmd, interpreter="python", executor="tmux", ports=[4444]
    )
    s.start()
    server = j.servers.openresty.get("test")
    server.install(reset=True)
    server.configure()
    website = server.websites.get("test3")
    website.ssl = False
    locations = website.locations.get("websocket_proxied")
    proxy_location = locations.locations_proxy.new()
    proxy_location.name = "proxy2"
    proxy_location.path_url = "/"
    proxy_location.ipaddr_dest = "0.0.0.0"
    proxy_location.port_dest = "4444"
    proxy_location.type = "websocket"
    proxy_location.scheme = "http"
    locations.configure()
    website.configure()
    server.start()

    from websocket import WebSocket

    ws = WebSocket()
    ws.connect("ws://0.0.0.0/")
    assert ws.connected
