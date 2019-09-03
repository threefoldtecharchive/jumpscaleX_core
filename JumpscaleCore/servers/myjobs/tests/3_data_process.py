import gevent
from Jumpscale import j


def main(self, start=True, count=20):
    """
    kosmos -p 'j.servers.myjobs.test("data_process")'
    """
    if start:
        self.workers_tmux_start(4)

    def wait_1sec():
        gevent.sleep(1)
        return "OK"

    ids = []
    self._data_process_untill_empty()
    for x in range(count):
        job_sch = j.servers.myjobs.schedule(wait_1sec)
        ids.append(job_sch.id)

    print(ids)
    res = self.results(ids)
    for id in ids:
        assert res[id] == "OK"

    print("TEST OK")
