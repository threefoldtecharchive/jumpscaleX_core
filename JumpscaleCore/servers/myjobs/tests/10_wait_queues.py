import gevent
from Jumpscale import j

myjobs = j.servers.myjobs

skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/493")
def test_wait_queues(reset=False):

    """
    kosmos -p 'j.servers.myjobs.test("wait_queues")'
    """
    myjobs._test_setup()
    j.tools.logger.debug = True
    queue_a = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % "queue_a")
    queue_b = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % "queue_b")

    queue_a.reset()
    queue_b.reset()
    myjobs.workers_tmux_start()

    def add(a=None, b=None):
        return a + b

    ids = []
    for x in range(10):
        ids.append(myjobs.schedule(add, return_queues=["queue_a", "queue_b"], a=1, b=2))

    res = myjobs.results(ids=ids, return_queues=["queue_a", "queue_b"])
    assert len(res) == 10
    print(res)
    queue_a = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % "queue_a")
    queue_b = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % "queue_a")

    assert queue_a.qsize() == 0
    assert queue_b.qsize() == 0
    myjobs._test_teardown()
    print("wait TEST OK")
    print("TEST OK")
