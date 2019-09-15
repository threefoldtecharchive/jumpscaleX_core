from Jumpscale import j
from Jumpscale.sal.hostfile.HostFile import HostFile


TEST_HOSTSFILE = "/tmp/hosts"


def test_main(self=None):
    """
    to run:

    kosmos 'j.sal.hostfile._test(name="hostfile")'

    """
    try:
        hostfile = HostFile()
        if j.sal.fs.exists(TEST_HOSTSFILE):
            j.sal.fs.remove(TEST_HOSTSFILE)
        hostfile._host_filepath = TEST_HOSTSFILE
        j.sal.process.execute('echo "194.45.24.74 test" >> {}'.format(TEST_HOSTSFILE))
        assert hostfile.ip_exists("194.45.24.74") is True
        hostfile.hostnames_set("194.45.24.74", ["testhostname"])
        assert "testhostname" in hostfile.hostnames_get("194.45.24.74")
        hostfile.ip_remove("194.45.24.74")
        assert hostfile.ip_exists("194.45.24.74") is False
    finally:
        if j.sal.fs.exists(TEST_HOSTSFILE):
            j.sal.fs.remove(TEST_HOSTSFILE)
