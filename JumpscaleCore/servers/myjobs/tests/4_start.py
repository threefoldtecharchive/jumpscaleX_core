import gevent
from Jumpscale import j


myjobs = j.servers.myjobs

skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/493")
def test_start(count=10):
    """
    kosmos -p 'j.servers.myjobs.test("start")'
    """
    myjobs._test_setup()

    def wait_1sec():
        gevent.sleep(1)
        return "OK"

    ids = []
    for x in range(count):
        job_sch = myjobs.schedule(wait_1sec)
        ids.append(job_sch.id)

    myjobs._workers_gipc_nr_max = 10
    myjobs.workers_subprocess_start()

    res = myjobs.results(ids, timeout=120)

    print(res)
    myjobs._test_teardown()
    print("start TEST OK")
    print("TEST OK")
