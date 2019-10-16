from Jumpscale import j
from .Syncer import Syncer
import gevent


class SyncerFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.tools.syncer"

    _CHILDCLASS = Syncer

    def sync(self, monitor=False):
        """
        execute to sync all syncers
        will push default code directories to remove ssh host
        """

        syncs = j.tools.syncer.find()
        threads = [gevent.spawn(syncer.sync()) for syncer in syncs]
        gevent.joinall(threads)

    def test(self):
        """
        kosmos 'j.tools.syncer.test()'
        :return:
        """

        cl = j.clients.ssh.get(name="test1", addr="172.17.0.3", port=22)
        cl.save()

        cl2 = j.clients.ssh.get(name="test2", addr="172.17.0.3", port=22)
        cl2.save()

        s = j.tools.syncer.get()

        s.sshclients_add([cl, cl2])

        s.sync(monitor=True)
