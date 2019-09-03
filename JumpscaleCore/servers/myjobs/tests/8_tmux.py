import gevent

from Jumpscale import j

import time


def main(self):
    """
    kosmos -p 'j.servers.myjobs.test("tmux")'
    """

    # TODO: why does it take so long to get the workers responding on waiting?

    self.stop(reset=True)  # will make sure all tmux are gone
    assert len(self.find()) == 0

    self.workers_tmux_start(2)

    assert len(self.find()) == 2

    found = False
    timeend = j.data.time.epoch + 20
    while not found and j.data.time.epoch < timeend:
        found = [str(i.state) for i in self.find(reload=False)] == ["WAITING", "WAITING"]
        print([str(i.state) for i in self.find(reload=False)])
        time.sleep(0.1)

    assert found
    assert [i.nr for i in self.find()] == [1, 2]

    start = j.data.time.epoch
    self.workers_tmux_start(2)
    # means the tmux did not restart as it should, because its functional
    assert j.data.time.epoch < start + 1

    def wait_1sec():
        gevent.sleep(1)
        return "OK"

    ids = []
    self._data_process_untill_empty()
    for x in range(4):
        ids.append(j.servers.myjobs.schedule(wait_1sec))

    res = self.results(ids)
    for id in ids:
        assert res[id] == "OK"

    start = j.data.time.epoch
    self.workers_tmux_start(2)
    # means the tmux did not restart as it should, because its functional
    assert j.data.time.epoch < start + 1

    print("TEST OK FOR TMUX")
