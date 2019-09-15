import gevent
from Jumpscale import j


def main(self, reset=False):

    """
    kosmos -p 'j.servers.myjobs.test("wait")'
    """
    # TODO: this behaviour should be reimplemented withouth return queues
    return

    if reset:
        self.reset()

    def add(a=None, b=None):
        return a + b

    ids = []
    for x in range(10):
        ids.append(self.schedule(add, a=1, b=2, return_queues=["q1"], return_queues_reset=True))

    self.workers_tmux_start()

    print("here")
    res = self.wait(queue_name="q1", size=10, returnjobs=True)
    assert len(res) == 10

    res = self.results(ids, timeout=120)
    print(res)

    # self.reset()
    #
    # ids = []
    # for x in range(10):
    #     ids.append(self.schedule(add, 1, 2, return_queues=["q2"], return_queues_reset=True))
    #
    # self.workers_subprocess_start()
    #
    # q = self.wait(queue_name="q2", size=11, timeout=5)
    # assert q is None

    print("TEST OK")
