import subprocess

from Jumpscale import j

JSBASE = j.baseclasses.object
TESTTOOLS = j.baseclasses.testtools


class TLS(JSBASE, TESTTOOLS):
    def _init(self, **kwargs):
        self.cwd = j.tools.path.get(kwargs["path"])

    def subjects_ask(self):
        """
        Ask questions for names arguments
        :return: a list of dict like :
         [{
            'C': 'AE',
            'L': 'Dubai',
            'O': 'GreenITGlobe',
            'OU': '0-complexity',
            'ST': 'Dubai',
            'CN': 'Common Name'
        }]
        :rtype: list
        """
        country = j.tools.console.askString("Country", "AE")
        location = j.tools.console.askString("Location", "Dubai")
        organisation = j.tools.console.askString("Organisation", "GreenITGlobe")
        org_unit = j.tools.console.askString("Organisation Unit", "0-complexity")
        state = j.tools.console.askString("State", "Dubai")
        common_name = j.tools.console.askString("common_name")
        return [{"C": country, "L": location, "O": organisation, "OU": org_unit, "ST": state, "CN": common_name}]

    def ca_create(self, subjects, key_algo="rsa", key_size=4096):
        """Generate a Root CA.

        :param subjects: list of dicts containing valid csr names. It can be created with subjects_ask method.
        :type subjects: dict
        :param key_algo: name of the algorithm to use to for key generation, defaults to 'rsa'
        :type key_algo: str, optional
        :param key_size: size of the key to generate, defaults to 4096
        :type key_size: int, optional
        :return: (path_to_cert, path_to_key)
        :rtype: set
        """
        csr = self._csr_get(subjects, None, key_algo, key_size)
        ca_csr_path = self.cwd.joinpath("ca-csr.json")
        ca_cert_path = self.cwd.joinpath("root-ca")
        ca_csr_path.write_text(j.data.serializers.json.dumps(csr, indent=4))

        subprocess.run(
            "cfssl gencert -initca %s | cfssljson -bare %s" % (ca_csr_path, ca_cert_path), shell=True, check=True
        )

        cert_path = ca_cert_path + ".pem"
        key_path = ca_cert_path + "-key.pem"
        output = "certificate generated at %s and key at %s" % (cert_path, key_path)
        self._log_debug(output)

        return (cert_path, key_path)

    def csr_create(self, name, subjects, hosts, key_algo="rsa", key_size=2048):
        """Create csr file and key

        :param name: name to indentify the csr
        :type name: str
        :param subjects: list of dicts containing valid csr names. It can be created with subjects_ask method.
        :type subjects: list
        :param hosts: list of the domain names which the certificate should be valid for
        :type hosts: list
        :param key_algo: name of the algorithm to use to for key generation, defaults to 'rsa'
        :type key_algo: str, optional
        :param key_size: size of the key to generate, defaults to 2048
        :type key_size: int, optional
        :return: (path_to_csr, path_to_key)
        :rtype: set
        """
        csr = self._csr_get(subjects, hosts, key_algo, key_size)
        csr_json_path = self.cwd.joinpath("%s.json" % name)
        csr_json_path.write_text(j.data.serializers.json.dumps(csr, indent=4))

        output_path = self.cwd.joinpath(name)
        subprocess.run("cfssl genkey %s | cfssljson -bare %s" % (csr_json_path, output_path), shell=True, check=True)

        csr_path = self.cwd.joinpath("%s.csr" % name)
        key_path = self.cwd.joinpath("%s-key.pem" % name)
        output = "certificate signing request generated at %s and key at %s" % (csr_path, key_path)
        self._log_debug(output)

        return (csr_path, key_path)

    def csr_sign(self, csr, ca, ca_key):
        """Sign csr certificate

        :param csr: path to the csr filee to sign
        :type csr: str
        :param ca: path to the ca certificate
        :type ca: str
        :param ca_key: path to the ca key
        :type ca_key: str
        :return: the signed certificate
        :rtype: str
        """
        base = j.tools.path.get(csr.rstrip("/")).basename()
        name = base.split(".")[0]

        output_path = self.cwd.joinpath(name)
        subprocess.run(
            "cfssl sign -ca %s -ca-key %s %s | cfssljson -bare %s" % (ca, ca_key, csr, output_path),
            shell=True,
            check=True,
        )
        cert_path = self.cwd.joinpath("%s.pem" % name)
        output = "certificate created at %s" % cert_path

        self._log_debug(output)

        return cert_path

    def signedcertificate_create(self, name, subjects, hosts, ca, ca_key, key_algo="rsa", key_size=2048):
        """
        signedcertificate_create is a helper that create a CSR and sign it with the given CA in one operation.

        :param name: name to indentify the csr
        :type name: str
        :param subjects: list of dicts containing valid csr names. It can be created with subjects_ask method.
        :type subjects: list
        :param hosts: list of the domain names which the certificate should be valid for
        :type hosts: list
        :param ca: path to the ca certificate
        :type ca: str
        :param ca_key: path to the ca key
        :type ca_key: str
        :param key_algo: name of the algorithm to use to for key generation, defaults to 'rsa'
        :type key_algo: str, optional
        :param key_size: size of the key to generate, defaults to 2048
        :type key_size: int, optional

        return (path_to_csr, path_to_key)
        """
        csr = self._csr_get(subjects, hosts, key_algo, key_size)
        csr_json_path = self.cwd.joinpath("%s.json" % name)
        csr_json_path.write_text(j.data.serializers.json.dumps(csr, indent=4))

        output_path = self.cwd.joinpath(name)
        subprocess.run(
            "cfssl gencert -ca %s -ca-key %s %s | cfssljson -bare %s" % (ca, ca_key, csr_json_path, output_path),
            shell=True,
            check=True,
        )

        cert_path = self.cwd.joinpath("%s.pem" % name)
        key_path = self.cwd.joinpath("%s-key.pem" % name)

        output = "certificate generated at %s and key at %s" % (cert_path, key_path)
        self._log_debug(output)

        return (cert_path, key_path)

    def _csr_get(self, subjects, hosts=None, key_algo="rsa", key_size=2048):
        """Helper function that returns the dict used for csr json

        :param subjects: list of dicts containing valid csr names. It can be created with subjects_ask method.
        :type subjects: list
        :param hosts: list of the domain names which the certificate should be valid for
        :type hosts: list
        :param key_algo: name of the algorithm to use to for key generation, defaults to 'rsa'
        :type key_algo: str, optional
        :param key_size: size of the key to generate, defaults to 2048
        :type key_size: int, optional
        :return: csr dict
        :rtype: dict
        """
        if not isinstance(subjects, list):
            subjects = [subjects]

        common_name = ""
        for s in subjects:
            common_name += "%s," % s["CN"]
            del s["CN"]
        common_name = common_name.rstrip(",")

        return {
            "hosts": hosts if hosts else [],
            "CN": common_name,
            "key": {"algo": key_algo, "size": key_size},
            "names": subjects,
        }

    def test(self, name=""):
        """Run tests under tests

        :param name: basename of the file to run, defaults to ''.
        :type name: str, optional
        """
        self._test_run(name=name, obj_key="test_main")
