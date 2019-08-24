import socket
import time
from Jumpscale import j
from netifaces import interfaces, ifaddresses

TEMPLATE = """
port = 8123
"""

JSConfigBase = j.baseclasses.object


class MulticastClient(JSConfigBase):
    def __init__(self, instance, data=None, parent=None, interactive=False):
        if not data:
            data = {}
        JSConfigBase.__init__(
            self, instance=instance, data=data, parent=parent, template=TEMPLATE, interactive=interactive
        )

    def send(self):
        # Get zerotier ipv6
        for iface_name in interfaces():
            if "zt" not in iface_name:
                continue
            while True:
                addresses = ifaddresses(iface_name).get(socket.AF_INET6)
                if not addresses:
                    time.sleep(5)
                else:
                    break
            bind_ip = addresses[0]["addr"]
            break
        else:
            raise j.exceptions.Base("You are not connected to zerotier")

        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.bind((bind_ip, 0))
        while True:
            data = str(time.time()).encode()
            # "ff02::1" is the multicast address which represents all nodes on the local network segment
            s.sendto(data, ("ff02::1", self.config.data["port"]))
            time.sleep(1)

    def listen(self):
        # Create a socket
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        # Bind it to the port
        s.bind(("", self.config.data["port"]))

        # Loop, printing any data we receive
        while True:
            data, sender_address = s.recvfrom(1500)
            while data[-1:] == "\0":
                data = data[:-1]  # Strip trailing \0's
            print(str(sender_address) + "  " + repr(data))
