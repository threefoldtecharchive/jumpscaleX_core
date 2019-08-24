import gevent


def main(self):

    self.reset()

    def add(a, b):
        return a + b

    ids = []
    for x in range(10):
        ids.append(self.schedule(add, 1, 2, return_queues=["q1"], return_queues_reset=True))

    self.start(subprocess=True)

    print("here")
    q = self.wait(queue_name="q1", size=10)
    assert q is not None

    res = self.results(ids, timeout=120)
    print(res)

    self.reset()

    ids = []
    for x in range(10):
        ids.append(self.schedule(add, 1, 2, return_queues=["q2"], return_queues_reset=True))

    self.start(subprocess=True)

    q = self.wait(queue_name="q2", size=11, timeout=5)
    assert q is None

    print("TEST OK")
