import gevent

from Jumpscale import j

import time


def main(self):
    """
    kosmos -p 'j.servers.myjobs.test("tmux")'
    """

    self.stop(reset=True)  # will make sure all tmux are gone
    assert len(self.workers.find()) == 0

    self.workers_tmux_start(2)

    assert len(self.workers.find()) == 2

    found = False
    timeend = j.data.time.epoch + 20
    while not found and j.data.time.epoch < timeend:
        found = [str(i.state) for i in self.workers.find(reload=False)] == ["WAITING", "WAITING"]
        print([str(i.state) for i in self.workers.find(reload=False)])
        time.sleep(3)

    assert found
    assert [i.nr for i in self.workers.find()] == [1, 2]

    self.workers_tmux_start(2)

    def wait_1sec():
        gevent.sleep(1)
        return "OK"

    ids = []
    for x in range(4):
        job_sch = j.servers.myjobs.schedule(wait_1sec)
        ids.append(job_sch.id)

    res = self.results(ids)
    for id in ids:
        assert res[id] == "OK"

    self.workers_tmux_start(2)

    assert self.workers.w1.state == "WAITING"

    self.workers.w1.stop()

    found = False
    timeend = j.data.time.epoch + 40
    while not found and j.data.time.epoch < timeend:
        found = self.workers.w1.state == "HALTED"
        time.sleep(5)
        self._log("waiting stop:%s" % self.workers.w1.state)

    assert found

    assert self.workers.w1.nr == 1
    assert self.workers.w1.pid == 0
    assert self.workers.w1.state == "HALTED"

    assert self.workers.w2.nr == 2
    assert self.workers.w2.pid > 0
    assert self.workers.w2.state == "WAITING"

    print("TEST OK FOR TMUX")
