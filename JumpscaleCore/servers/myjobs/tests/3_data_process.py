import gevent

from Jumpscale import j


def main(self, start=True, count=20):
    if start:
        self.workers_start_tmux(4)

    def wait_1sec():
        gevent.sleep(1)
        return "OK"

    ids = []
    self._data_process_untill_empty()
    for x in range(count):
        ids.append(j.servers.myjobs.schedule(wait_1sec))

    print(ids)

    res = self.results(ids)
    for id in ids:
        assert res[id] == "OK"

    print("TEST OK")
