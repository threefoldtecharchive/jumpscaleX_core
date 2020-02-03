import gevent

from Jumpscale import j

import time

myjobs = j.servers.myjobs

skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/493")
def test_tmux():
    """
    kosmos -p 'j.servers.myjobs.test("tmux")'
    """
    myjobs._test_setup()
    assert len(myjobs.workers.find()) == 0

    myjobs.workers_tmux_start(2)

    assert len(myjobs.workers.find()) == 2

    found = False
    timeend = j.data.time.epoch + 20
    while not found and j.data.time.epoch < timeend:
        found = [str(i.state) for i in myjobs.workers.find(reload=False)] == ["WAITING", "WAITING"]
        print([str(i.state) for i in myjobs.workers.find(reload=False)])
        time.sleep(3)

    assert found
    assert [i.nr for i in myjobs.workers.find()] == [1, 2]

    myjobs.workers_tmux_start(2)

    def wait_1sec():
        gevent.sleep(1)
        return "OK"

    ids = []
    for x in range(4):
        job_sch = j.servers.myjobs.schedule(wait_1sec)
        ids.append(job_sch.id)

    res = myjobs.results(ids)
    for item in res:
        assert item == "OK"
    assert len(res) == len(ids)
    myjobs.workers_tmux_start(2)

    assert myjobs.workers.w1.state == "WAITING"

    myjobs.workers.w1.stop()

    found = False
    timeend = j.data.time.epoch + 40
    while not found and j.data.time.epoch < timeend:
        found = myjobs.workers.w1.state == "HALTED"
        time.sleep(5)
        myjobs._log("waiting stop:%s" % myjobs.workers.w1.state)

    assert found

    assert myjobs.workers.w1.nr == 1
    assert myjobs.workers.w1.pid == 0
    assert myjobs.workers.w1.state == "HALTED"

    assert myjobs.workers.w2.nr == 2
    assert myjobs.workers.w2.pid > 0
    assert myjobs.workers.w2.state == "WAITING"
    myjobs._test_teardown()
    print("Tmux TEST OK")
    print("TEST OK FOR TMUX")
