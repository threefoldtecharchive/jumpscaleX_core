from Jumpscale import j
from .TLS import TLS

JSBASE = j.baseclasses.object
TESTTOOLS = j.baseclasses.testtools


class TLSFactory(JSBASE, TESTTOOLS):
    """Factory class to deal with TLS, key and certificate generation"""

    __jslocation__ = "j.sal.tls"

    def get(self, path=None):
        """Get an instance of the TLS class
            This module use the cfssl AYS.

        :param path: Path is the working directory where the certificate and key will be generated, defaults to None
        :type path: string, optional
        :return: TLS instance
        :rtype: TLS class
        """
        return TLS(path=path)

    def test(self, name=""):
        """Run tests under tests

        :param name: basename of the file to run, defaults to ''.
        :type name: str, optional
        """
        self._tests_run(name=name)
