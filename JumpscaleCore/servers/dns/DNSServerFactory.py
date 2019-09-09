from gevent import socket
from pprint import pprint
from .DNSServer import DNSServers
from .DNSResolver import DNSResolvers

import os

from Jumpscale import j

JSBASE = j.baseclasses.object

# http://mirror1.malwaredomains.com/files/justdomains  domains we should not query, lets download & put in redis core
# https://blog.cryptoaustralia.org.au/2017/12/05/build-your-private-dns-server/


class DNSServerFactory(j.baseclasses.factory_testtools):

    _CHILDCLASSES = [DNSServers, DNSResolvers]
    __jslocation__ = "j.servers.dns"

    def _init(self, **kwargs):
        self._extensions = {}

    def get_gevent_server(self, name="default", port=53, bcdb_name="system", resolvername="default"):
        s = self.servers.get(name=name, port=port, resolvername=resolvername)
        # make sure there is a resolver created
        if resolvername == "default" and self.resolvers.exists(name=resolvername) == False:
            r = self.resolvers.new(name="default")
            r.save()
        s.save()
        return s

    def start(self, port=53, background=False):

        """
        js_shell 'j.servers.dns.start()'
        """
        if background:
            if j.core.platformtype.myplatform.platform_is_osx and port < 1025:
                pprint("PLEASE GO TO TMUX SESSION, GIVE IN PASSWD FOR SUDO, do tmux a")
                cmd = "sudo js_shell 'j.servers.dns.start(background=False,port=%s)'" % port
            else:
                cmd = "js_shell 'j.servers.dns.start(background=False,port=%s)'" % port
            j.servers.tmux.execute(cmd, window="dnsserver", pane="main", reset=False)
            self._log_info("waiting for uidserver to start on port %s" % port)
            res = j.sal.nettools.waitConnectionTest("localhost", port)

        if not background:

            rack = j.servers.rack.get()

            server = self.get_gevent_server(port=port)

            rack.add("dns", server)

            rack.start()
        else:
            # the MONKEY PATCH STATEMENT IS NOT THE BEST, but prob required for now
            S = """
            from gevent import monkey
            monkey.patch_all(subprocess=False)
            from Jumpscale import j
            j.servers.dns.start(port={port})
            """
            args = {"port": port}
            S = j.core.tools.text_replace(S, args)

            s = j.servers.startupcmd.new(name="dnsserver")
            s.cmd_start = S
            s.executor = "tmux"
            s.interpreter = "python"
            s.timeout = 10
            s.ports_udp = [port]
            s.start(reset=True)

    @property
    def dns_extensions(self):
        """
        all known extensions on http://data.iana.org/TLD/tlds-alpha-by-domain.txt
        """
        if self._extensions == {}:
            path = os.path.join(os.path.dirname(__file__), "knownextensions.txt")
            for line in j.sal.fs.readFile(path).split("\n"):
                if line.strip() == "" or line[0] == "#":
                    continue
                self._extensions[line] = True
        return self._extensions

    def test(self, start=True, port=5354):
        """
        kosmos 'j.servers.dns.test()'
        kosmos 'j.servers.dns.test(start=False)'
        """

        if start or not self.ping(port=port):
            self.start(background=True, port=port)

        ns = j.tools.dnstools.get(["localhost"], port=port)

        pprint(ns.namerecords_get("google.com"))
        pprint(ns.namerecords_get("info.despiegk"))

        bcdb = j.data.bcdb.new("test_dns")
        dns = self.get(port, bcdb)
        obj = dns.resolver.model.find(zone="test.com")
        if obj:
            obj[0].delete()

        dns.resolver.create_record(domain="one.test.com")
        assert "one.test.com" == dns.resolver.get_record(domain="one.test.com").domain

        dns.resolver.create_record(domain="two.test.com")
        assert "two.test.com" == dns.resolver.get_record(domain="two.test.com").domain

        dns.resolver.create_record(domain="one.test.com", ttl=360)
        assert 360 == dns.resolver.get_record(domain="one.test.com").ttl

        records = dns.resolver.model.find(zone="test.com")
        assert len(records) == 1

        record = records[0]
        assert len(record.domains) == 2

        dns.resolver.delete_record("two.test.com")

        records = dns.resolver.model.find(zone="test.com")
        assert len(records) == 1

        record = records[0]
        assert len(record.domains) == 1

        dns.resolver.delete_record("one.test.com")
        records = dns.resolver.model.find(zone="test.com")
        assert len(records) == 0
