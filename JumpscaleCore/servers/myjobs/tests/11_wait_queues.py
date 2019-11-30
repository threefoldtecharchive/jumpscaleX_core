import gevent
from Jumpscale import j


def main(self, reset=False):

    """
    kosmos -p 'j.servers.myjobs.test("wait_queues")'
    """
    j.tools.logger.debug = True
    queue_a = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % "queue_a")
    queue_b = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % "queue_b")

    queue_a.reset()
    queue_b.reset()
    self.reset()
    self.workers_tmux_start()

    def add(a=None, b=None):
        return a + b

    ids = []
    for x in range(10):
        ids.append(self.schedule(add, return_queues=["queue_a", "queue_b"], a=1, b=2))

    res = self.results(ids=ids, return_queues=["queue_a", "queue_b"])
    assert len(res) == 10
    print(res)
    queue_a = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % "queue_a")
    queue_b = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % "queue_a")

    assert queue_a.qsize() == 0
    assert queue_b.qsize() == 0

    print("wait TEST OK")
    print("TEST OK")
