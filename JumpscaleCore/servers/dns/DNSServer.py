from Jumpscale import j
import dnslib

from gevent.server import DatagramServer
from .DNSResolver import DNSResolver
from gevent import socket


# soaexample = dnslib.SOA(
#     mname="ns1.example.com",  # primary name server
#     rname="info.example.com",  # email of the domain administrator
#     times=(
#         201307231,  # serial number
#         60 * 60 * 1,  # refresh
#         60 * 60 * 3,  # retry
#         60 * 60 * 24,  # expire
#         60 * 60 * 1,  # minimum
#     ),
# )

# see https://github.com/andreif/dnslib  for more info how to use the lib


class DNSServer(DatagramServer, j.baseclasses.object_config):

    _SCHEMATEXT = """
    @url = jumpscale.dnsserver.1
    name** = ""
    port = 53
    addr = "127.0.0.1"
    resolvername = "main"
    """

    def __init__(self, **kwargs):
        j.baseclasses.object_config.__init__(self, **kwargs)

    def _init(self, **kwargs):

        DatagramServer.__init__(self, ":%s" % self.port, handle=self.handle)

        self.socket = self.get_listener(self.address, self.family)
        self.address = self.socket.getsockname()
        self._socket = self.socket
        try:
            self._socket = self._socket._sock
        except AttributeError:
            pass

        self.TTL = 60 * 5

        self.rtypes = {}
        self.rtypes["A"] = dnslib.QTYPE.A
        self.rtypes["AAAA"] = dnslib.QTYPE.AAAA
        self.rtypes["NS"] = dnslib.QTYPE.NS
        self.rtypes["MX"] = dnslib.QTYPE.MX

        self.rdatatypes = {}
        self.rdatatypes["A"] = dnslib.A
        self.rdatatypes["AAAA"] = dnslib.AAAA
        self.rdatatypes["NS"] = dnslib.NS
        self.rdatatypes["MX"] = dnslib.MX
        self._resolver = None

    @property
    def resolver(self):
        if not self._resolver:
            self._resolver = j.servers.dns.resolvers.get(name=self.resolvername)
        return self._resolver

    # def start(self):
    #     self.serve_forever()

    def handle(self, data, address):
        # self._log_debug('%s: got %r' % (address[0], data))
        if data == b"PING":
            self.sendback(b"PONG", address)
        else:
            # self.sendback(b"ERROR", address)
            # print len(data), data.encode('hex')
            resp = self.dns_response(data)
            self.sendback(resp, address)

    def sendback(self, data, address):
        try:
            self.socket.sendto(data, address)
        except Exception as e:
            self._log_error("error in communication:%s" % e)

    def resolve(self, qname, type="A"):
        def do(qname, type):
            name = str(qname).rstrip(".")
            if name.split(".")[-1].upper() in j.servers.dns.dns_extensions:
                res = []
                local_resolve = self.resolver.get_record(name, type)
                if local_resolve:
                    res.append(local_resolve.value)
                else:
                    try:
                        resp = j.tools.dnstools.default.resolver.query(name, type)
                    except Exception as e:
                        if "NoAnswer" in str(e):
                            self._log_warning("did not find:%s" % qname)
                            return []
                        self._log_error("could not resolve:%s (%s)" % (e, qname))
                        return []
                    for rr in resp:
                        if type == "A":
                            res.append(rr.address)
                        elif type == "AAAA":
                            self._log_debug("AAAA")
                            res.append(rr.address)
                        else:
                            res.append(str(rr.target))

                return res
            else:
                if type == "NS":
                    return ["127.0.0.1"]
                else:
                    return ["192.168.1.1"]
                # TODO: need to get DNS records from a source

        # self._cache.reset() #basically don't use cache, just for debugging later should disable this line
        res = self._cache.get(key="resolve_%s_%s" % (qname, type), method=do, expire=600, qname=qname, type=type)

        return res

    def dns_response(self, data):

        request = dnslib.DNSRecord.parse(data)

        self._log_debug("request:%s" % request)

        reply = dnslib.DNSRecord(dnslib.DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)

        qname = request.q.qname
        qn = str(qname)
        qtype = request.q.qtype
        qt = dnslib.QTYPE[qtype]

        addrs = self.resolve(qname, qt)

        if qt in ["A", "MX", "NS", "AAAA"]:
            for item in addrs:
                reply.add_answer(
                    dnslib.RR(
                        rname=qname, rtype=self.rtypes[qt], rclass=1, ttl=self.TTL, rdata=self.rdatatypes[qt](item)
                    )
                )
                self._log_debug("DNS reply:%s:%s" % (qt, reply))
        else:
            # TODO:*1 add the other record types e.g. SOA & txt & ...
            self._log_error("did not find type:\n%s" % request)

        return reply.pack()

    def ping(self):

        address = (self.addr, self.port)
        message = b"PING"
        sock = socket.socket(type=socket.SOCK_DGRAM)
        sock.connect(address)
        self._log_info("Sending %s bytes to %s:%s" % ((len(message),) + address))
        sock.send(message)
        try:
            data, address = sock.recvfrom(8192)
        except Exception as e:
            if "refused" in str(e):
                return False
            raise j.exceptions.Base("unexpected result")
        return True


class DNSServers(j.baseclasses.object_config_collection):
    _name = "servers"
    _CHILDCLASS = DNSServer
