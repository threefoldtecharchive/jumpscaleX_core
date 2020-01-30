import gevent
from Jumpscale import j

myjobs = j.servers.myjobs


def test_wait(reset=False):

    """
    kosmos -p 'j.servers.myjobs.test("wait")'
    """
    myjobs._test_setup()

    myjobs.workers_tmux_start()

    def add(a=None, b=None):
        return a + b

    def div(a=None, b=None):
        return a / b

    ids = []
    for x in range(10):
        ids.append(myjobs.schedule(add, a=1, b=2))

    res = myjobs.wait(ids=ids)
    assert len(res) == 10
    print(res)

    # user results instead of wait() which is basically the same!
    myjobs.workers_tmux_start()
    ids = []
    for x in range(10):
        ids.append(myjobs.schedule(add, a=1, b=2))
    res = myjobs.results(ids=ids)
    assert len(res) == 10
    res = myjobs.results(ids, timeout=120)
    print(res)

    # Test die
    myjobs.workers_tmux_start()
    ids = []
    for x in range(9):
        ids.append(myjobs.schedule(add, a=1, b=2))

    ids.append(myjobs.schedule(div, a=1, b=0))
    res = []
    try:
        res = myjobs.wait(ids=ids, die=True)
        raise AssertionError("should have died")
    except j.exceptions.Base:
        pass

    assert len(res) == 0
    myjobs._test_teardown()
    print("wait TEST OK")
    print("TEST OK")
