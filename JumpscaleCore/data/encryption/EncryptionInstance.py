from Jumpscale import j
import nacl.secret
import nacl.utils


class EncryptionInstance(j.baseclasses.object_config):

    _SCHEMATEXT = """
    @url = jumpscale.encryption.instance
    name** = "" (S)
    secret_ = "" (S)
    """

    def _init(self, **kwargs):
        if not self.secret_:
            raise j.exceptions.Input("provide secret_ please")
        secret2 = j.data.hash.md5_string(self.secret_).encode()
        self._box = nacl.secret.SecretBox(secret2)

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self._box.encrypt(data)

    def decrypt(self, data, binary=False):
        if isinstance(data, str):
            j.shell()
        r = self._box.decrypt(data)
        if not binary:
            return r.decode("utf-8")
        else:
            return r
