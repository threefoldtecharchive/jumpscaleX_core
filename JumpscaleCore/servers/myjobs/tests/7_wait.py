import gevent
from Jumpscale import j


def main(self, reset=False):

    """
    kosmos -p 'j.servers.myjobs.test("wait")'
    """
    self._test_setup()

    self.workers_tmux_start()

    def add(a=None, b=None):
        return a + b

    def div(a=None, b=None):
        return a / b

    ids = []
    for x in range(10):
        ids.append(self.schedule(add, a=1, b=2))

    res = self.wait(ids=ids)
    assert len(res) == 10
    print(res)

    # user results instead of wait() which is basically the same!
    self.workers_tmux_start()
    ids = []
    for x in range(10):
        ids.append(self.schedule(add, a=1, b=2))
    res = self.results(ids=ids)
    assert len(res) == 10
    res = self.results(ids, timeout=120)
    print(res)

    # Test die
    self.workers_tmux_start()
    ids = []
    for x in range(9):
        ids.append(self.schedule(add, a=1, b=2))

    ids.append(self.schedule(div, a=1, b=0))
    res = []
    try:
        res = self.wait(ids=ids, die=True)
        raise AssertionError("should have died")
    except j.exceptions.Base:
        pass

    assert len(res) == 0
    self._test_teardown()
    print("wait TEST OK")
    print("TEST OK")
