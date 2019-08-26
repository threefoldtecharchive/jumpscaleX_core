from Jumpscale import j
from .SonicServer import SonicServer

JSConfigs = j.baseclasses.object_config_collection


class SonicFactory(JSConfigs):
    """
    Open Publish factory
    """

    __jslocation__ = "j.servers.sonic"
    _CHILDCLASS = SonicServer

    def _init(self, **kwargs):
        self._default = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get(name="default")
        return self._default

    @property
    def bcdb(self):
        if not self._default:
            self._default = self.new(name="bcdb")
        return self._default

    def install(self, reset=False):
        """
        kosmos 'j.servers.sonic.build()'
        """
        j.builders.apps.sonic.install(reset=reset)

    def test(self, start=True):
        """
        kosmos 'j.servers.sonic.test()'
        :return:
        """
        self.install()
        s = self.get(name="test_instance")
        s.save()
        if start:
            s.start()

        client = s.default_client

        data = {
            "post:1": "this is some test text hello",
            "post:2": "this is a hello world post",
            "post:3": "hello how is it going?",
            "post:4": "for the love of god?",
            "post:5": "for the love lorde?",
        }

        for articleid, content in data.items():
            client.push("forum", "posts", articleid, content)

        assert client.query("forum", "posts", "love") == ["post:5", "post:4"]
