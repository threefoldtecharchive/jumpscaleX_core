from Jumpscale import j
from .BCDBModelClient import BCDBModelClient

skip = j.baseclasses.testtools._skip


class BCDBModelClientFactory(j.baseclasses.object):

    __jslocation__ = "j.clients.bcdbmodel"

    def _init(self, **kwargs):
        self._clients = j.baseclasses.dict()
        self._rediscl__ = None
        self._class = BCDBModelClient

    @property
    def _rediscl_(self):
        if not self._rediscl__:
            self._rediscl__ = j.clients.redis.get(port=6380)
        return self._rediscl__

    def server_config_reload(self):
        r = self._rediscl_.execute_command("bcdb_model_init", "", "", "", "")

    def get(self, url=None, schema=None, name=None):
        """
        :param name
        :return:
        """
        if schema:
            assert not url
            if isinstance(schema, str):
                schema = j.data.schema.get_from_text(schema)
            url = schema.url
        if not name:
            name = "system"
        if not url and not schema:
            raise j.exceptions.Input("need to specify url or schema")
        key = f"{name}_{url}"
        if key not in self._clients:
            if name != "system" and not j.data.bcdb.exists(name):
                raise j.exceptions.Input("bcdb:'%s' has not been configured yet" % name)
            self._clients[key] = BCDBModelClient(name=name, url=url)
        return self._clients[key]

    @property
    def schemas(self):
        res = {}
        for name, bcdb in j.data.bcdb.instances.items():
            models = res.get(name, [])
            for model in bcdb.models:
                models.append(model)
            res[name] = models
        return res

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/531")
    def test(self):
        """
        kosmos -p 'j.clients.bcdbmodel.test()'
        :return:
        """

        # j.servers.threebot.start(background=True)

        b = j.clients.bcdbmodel.get(url="jumpscale.sshclient.1")

        print(b.find())

        obj = b.find()[0]

        obj = b.get(id=obj.id)
        obj.addr = "localhost:%s" % j.data.idgenerator.generateRandomInt(1, 100000)
        obj.save()

        obj2 = b.get(id=obj.id)

        assert obj2.addr == obj.addr

        print("TEST OK")
