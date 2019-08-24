import subprocess
from Jumpscale import j
from Jumpscale.sal.ssl.SSLFactory import SSLFactory

SSLFactory = SSLFactory()


def ca_generate():

    """
    test_ca_geneerate uses ca_cert_generate to generate ca certificate 
    in cert_dir directory
    """

    SSLFactory.ca_cert_generate("/tmp/test/")
    file_list = subprocess.run("ls -la /tmp/test/", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    files = file_list.stdout.decode()
    assert "ca.key" in files
    assert "ca.crt" in files


def verify():

    """
    It reads the pathes of certificate and key files of an X509 certificate
    and verify if certificate matches private key
    """

    output = SSLFactory.verify("/tmp/test/ca.crt", "/tmp/test/ca.key")
    assert output is True


def certificate_signing_request_create():

    """
    Creating CSR (Certificate Signing Request)
    this CSR normally passed to the CA (Certificate Authority) to create a signed certificate
    """

    output = SSLFactory.certificate_signing_request_create("test")
    assert "BEGIN PRIVATE KEY" in str(output)
    assert "END PRIVATE KEY" in str(output)
    assert "BEGIN CERTIFICATE REQUEST" in str(output)
    assert "END CERTIFICATE REQUEST" in str(output)


def test_main(self=None):
    """ to run:
     kosmos 'j.sal.ssl._test(name="ssl")'

    """
    ca_generate()
    verify()
    certificate_signing_request_create()
