from __future__ import print_function
from Jumpscale import j


try:
    import dns
    import dns.message
    import dns.rdataclass
    import dns.rdatatype
    import dns.query
    import dns.resolver
except Exception as e:
    print("WARNING install dnspython: 'pip3 install dnspython'")

JSBASE = j.baseclasses.object


class DNSTools(j.baseclasses.object):
    """
    to install:
    pip3 install dnspython
    """

    __jslocation__ = "j.tools.dnstools"
    __import__ = "dnspython"

    def _init(self, **kwargs):
        self._default = None

    def get(
        self, nameservers=["8.8.8.8", "8.8.4.4"], port=53
    ):  # https://www.computerworld.com/article/2872700/endpoint-security/6-dns-services-protect-against-malware-and-other-unwanted-content.html?page=3
        if "localhost" in nameservers:
            nameservers.pop(nameservers.index("localhost"))
            nameservers.append("127.0.0.1")
        return DNSClient(nameservers=nameservers, port=port)

    @property
    def default(self):
        if self._default == None:
            self._default = self.get()

        return self._default

    def test(self, start=False):
        """
        kosmos 'j.tools.dnstools.test()'
        """

        answer = self.default.resolver.query("www.yelp.com", "A")


class DNSClient(j.baseclasses.object):
    def __init__(self, nameservers, port=53):
        JSBASE.__init__(self)
        self.nameservers = nameservers
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.nameservers = self.nameservers
        self.resolver.port = port

    def nameservers_get(self, domain="threefoldtoken.org"):

        answer = self.resolver.query(domain, "NS")

        res = []
        for rr in answer:
            res.append(rr.target.to_text())
        return res

    def namerecords_get(self, dnsurl="www.threefoldtoken.org"):
        """
        return ip addr for a full name
        """

        answer = self.resolver.query(dnsurl, "A")

        res = []
        for rr in answer:
            res.append(rr.address)
        return res
