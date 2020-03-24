from Jumpscale import j
from .SonicClient import SonicClient

JSConfigs = j.baseclasses.object_config_collection

skip = j.baseclasses.testtools._skip


class SonicFactory(JSConfigs, j.baseclasses.testtools):

    """
    Sonic Client factory
    """

    __jslocation__ = "j.clients.sonic"
    _CHILDCLASS = SonicClient

    def get_client_bcdb(self):
        """
        j.clients.sonic.get_client_bcdb()
        :return:
        """
        adminsecret_ = j.core.myenv.adminsecret
        if j.core.myenv.testing_env:
            return self.get("bcdb", host="127.0.0.1", port=1492, password="123456")  # default passwd also not ok
        else:
            return self.get("bcdb", host="127.0.0.1", port=1491, password=adminsecret_)  # default passwd also not ok

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/570")
    def test(self):
        """
        kosmos 'j.clients.sonic.test()'
        :return:
        """
        j.builders.apps.sonic.install()
        j.servers.sonic.default.start()
        data = {
            "post:1": "this is some test text hello",
            "post:2": "this is a hello world post",
            "post:3": "hello how is it going?",
            "post:4": "for the love of god?",
            "post:5": "for the love lorde?",
        }
        client = self.get("test", host="127.0.0.1", port=1491, password="123456")
        for articleid, content in data.items():
            client.push("forum", "posts", articleid, content)
        assert client.query("forum", "posts", "love") == ["post:5", "post:4"]

        print("TEST OK")

    def test_sonic(self, name=""):
        self._tests_run(name=name, die=True)
