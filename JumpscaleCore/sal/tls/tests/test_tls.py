import subprocess
import pytest

from Jumpscale.sal.tls.TLS import TLS
from Jumpscale import j

SUBJECTS = {"C": "AE", "L": "Dubai", "O": "GreenITGlobe", "OU": "0-complexity", "ST": "Dubai", "CN": "test.com"}


def full_flow():
    j.sal.fs.createDir("/tmp/testtls")
    tls = TLS(path="/tmp/testtls")

    ca, ca_key = tls.ca_create(dict(SUBJECTS))
    assert j.sal.fs.exists(ca)
    assert j.sal.fs.exists(ca_key)

    csr, csr_key = tls.csr_create("test", dict(SUBJECTS), ["test.com"])
    assert j.sal.fs.exists(csr)
    assert j.sal.fs.exists(csr_key)

    path = tls.csr_sign(csr, ca, ca_key)
    assert j.sal.fs.exists(path)
    j.sal.fs.remove("/tmp/testtls")


def signedcert_flow():
    j.sal.fs.createDir("/tmp/testtls")
    tls = TLS(path="/tmp/testtls")

    ca, ca_key = tls.ca_create(dict(SUBJECTS))
    assert j.sal.fs.exists(ca)
    assert j.sal.fs.exists(ca_key)

    paths = tls.signedcertificate_create("test", dict(SUBJECTS), ["test.com"], ca, ca_key)
    for path in paths:
        assert j.sal.fs.exists(path)
    j.sal.fs.remove("/tmp/testtls")


@pytest.mark.integration
def test_main(self=None):
    """
    to run:

    kosmos 'j.sal.tls._test(name="tls")'

    """
    subprocess.run("curl https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 -o /usr/local/bin/cfssl", shell=True, check=True)
    subprocess.run(
        "curl https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64 -o /usr/local/bin/cfssljson", shell=True, check=True
    )
    subprocess.run("chmod +x /usr/local/bin/cfssl /usr/local/bin/cfssljson", shell=True, check=True)

    full_flow()
    signedcert_flow()
