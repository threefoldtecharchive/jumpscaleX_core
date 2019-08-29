from Jumpscale import j

from .RDBClient import RDBClient

#
JSBASE = j.baseclasses.object


class RDBFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.rdb"
    _CHILDCLASS = RDBClient

    def client_get(self, namespace="test", redisconfig_name="core", fromcache=True, redisclient=None):
        """
        :param nsname: namespace name
        :param redisconfig_name: name of the redis config client see j.clients.redis_config
        :return:
        """
        if not redisclient:
            redisclient = j.clients.redis_config.get_client(redisconfig_name, fromcache=fromcache)
            redisclient.redisconfig_name = redisconfig_name
        return RDBClient(nsname=namespace, redisclient=redisclient)

    def test(self):
        """
        kosmos 'j.clients.rdb.test()'

        """

        self._test_run(name="base")
