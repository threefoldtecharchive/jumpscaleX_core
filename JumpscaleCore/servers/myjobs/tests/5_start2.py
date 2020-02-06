import gevent
from Jumpscale import j

myjobs = j.servers.myjobs

skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/493")
def test_start2(count=20):
    """
    kosmos -p 'j.servers.myjobs.test("start2")'
    """

    myjobs._test_setup()
    myjobs.workers_subprocess_start()

    def wait_2sec():
        gevent.sleep(2)

    for x in range(count):
        myjobs.schedule(wait_2sec)

    assert myjobs._mainloop_gipc.ready()
    myjobs._test_teardown()
    print("start2 TEST OK")
    print("TEST OK")
