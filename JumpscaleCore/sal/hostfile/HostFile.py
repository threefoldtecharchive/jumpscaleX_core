# import time
# import socket
import re

from Jumpscale import j

JSBASE = j.baseclasses.object


class HostFile(JSBASE):
    __jslocation__ = "j.sal.hostsfile"

    def _init(self, **kwargs):
        self._host_filepath = "/etc/hosts"

    def ip_remove(self, ip):
        """Update a hostfile, delete ip from hostsfile
        :param ip: Ip of the machine to remove
        :type ip: string
        """
        # get content of hostsfile
        filecontents = j.sal.fs.readFile(self._host_filepath)
        search_obj = re.search("^%s\s.*\n" % ip, filecontents, re.MULTILINE)
        if search_obj:
            filecontents = filecontents.replace(search_obj.group(0), "")
            j.sal.fs.writeFile(self._host_filepath, filecontents)
        else:
            self._log_warning("Ip address %s not found in hosts file" % ip)

    def ip_exists(self, ip):
        """Check if ip is in the hostsfile
        :param ip: Ip of the machine to check
        :type ip: string
        :return: True if ip is in hostfile, False otherwise
        :rtype: bool
        """
        # get content of hostsfile
        filecontents = j.sal.fs.readFile(self._host_filepath)
        res = re.search("^%s\s" % ip, filecontents, re.MULTILINE)
        if res:
            return True
        else:
            return False

    def hostnames_get(self, ip):
        """Get hostnames for ip address
        :param ip: Ip of the machine to get hostnames from
        :type ip: string
        :return: list of hostnames
        :rtype: list
        """
        if self.ip_exists(ip):
            filecontents = j.sal.fs.readFile(self._host_filepath)
            search_obj = re.search("^%s\s.*\n" % ip, filecontents, re.MULTILINE)
            hostnames = search_obj.group(0).strip().split()
            hostnames.pop(0)
            return hostnames
        else:
            return []

    def hostnames_set(self, ip, hostnames):
        """Update a hostfile to contain the basic information install
        :param ip: Ip of the machine to add/modify
        :type ip: string
        :param hostnames: List of machinehostnames to add/modify
        :type hostnames: list of hostnames or a string of space-separated hostnames
        """
        if isinstance(hostnames, str):
            hostnames = hostnames.split()
        filecontents = j.sal.fs.readFile(self._host_filepath)
        search_obj = re.search("^%s\s.*\n" % ip, filecontents, re.MULTILINE)

        hostnames = " ".join(hostnames)
        if search_obj:
            filecontents = filecontents.replace(search_obj.group(0), "%s %s\n" % (ip, hostnames))
        else:
            filecontents += "%s %s\n" % (ip, hostnames)

        j.sal.fs.writeFile(self._host_filepath, filecontents)

    def _test(self, name=""):
        """Run tests under tests
        :param name: basename of the file to run, defaults to "".
        :type name: str, optional
        """
        self._test_run(name=name, obj_key="test_main")
