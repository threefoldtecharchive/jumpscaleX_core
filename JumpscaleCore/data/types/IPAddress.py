from .PrimitiveTypes import String
from .TypeBaseClasses import *
from Jumpscale import j

from ipaddress import IPv4Address, IPv6Address
from ipaddress import AddressValueError, NetmaskValueError


class IPAddress(String):
    """
    ipaddress can be v4 or v6
    """

    NAME = "ipaddr , ipaddress"

    def __init__(self, default=None):
        self.BASETYPE = "string"
        self._default = default

    def check(self, value):
        if value in ["", None]:
            return True
        if isinstance(value, str):
            if value.lower() == "localhost":
                return True
            return self.is_valid_ipv4(value) or self.is_valid_ipv6(value)
        else:
            return False

    def is_valid_ipv4(self, ip):
        """ Validates IPv4 addresses.
            https: // stackoverflow.com/questions/319279/
            the use of regular expressions is INSANE. and also wrong.
            use standard python3 ipaddress module instead.
        """
        try:
            return IPv4Address(ip) and True
        except (AddressValueError, NetmaskValueError):
            return False

    def is_valid_ipv6(self, ip):
        """ Validates IPv6 addresses.
            https: // stackoverflow.com/questions/319279/
            the use of regular expressions is INSANE. and also wrong.
            use standard python3 ipaddress module instead.
        """
        try:
            return IPv6Address(ip) and True
        except (AddressValueError, NetmaskValueError):
            return False

    def clean(self, value):
        if value is None or value is "":
            return self.default_get()
        if not self.check(value):
            raise j.exceptions.Value("invalid ip address %s" % value)
        else:
            if value.lower() == "localhost":
                value = "127.0.0.1"
            return value

    def default_get(self):
        if not self._default:
            self._default = "0.0.0.0"
        return self.fromString(self._default)

    def fromString(self, v):
        if not j.data.types.string.check(v):
            raise j.exceptions.Value("Input needs to be string:%s" % v)
        if self.check(v):
            return v
        else:
            raise j.exceptions.Value("%s not a valid ip'" % (v))
