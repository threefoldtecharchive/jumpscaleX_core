from Jumpscale import j
import gevent

myjob = j.servers.myjobs

skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/493")
def test_timeout():
    """
    kosmos -p 'j.servers.myjobs.test("timeout")'
    """
    myjob._test_setup()
    j.tools.logger.debug = True

    def add(a=None, b=None):
        gevent.sleep(2)
        assert a
        assert b
        return a + b

    job = myjob.schedule(add, a=1, b=2, timeout=1)

    myjob.worker_inprocess_start()
    job = myjob.wait([job.id], die=False)[0]
    assert job.state == "ERROR"
    assert job.error_cat == "TIMEOUT"
    myjob._test_teardown()
    print("timeout TEST OK")
    print("TEST OK")
