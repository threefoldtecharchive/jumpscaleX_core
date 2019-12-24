import gevent


def main(self, count=10):
    """
    kosmos -p 'j.servers.myjobs.test("start")'
    """
    self._test_setup()

    def wait_1sec():
        gevent.sleep(1)
        return "OK"

    ids = []
    for x in range(count):
        job_sch = self.schedule(wait_1sec)
        ids.append(job_sch.id)

    self._workers_gipc_nr_max = 10
    self.workers_subprocess_start()

    res = self.results(ids, timeout=120)

    print(res)
    self._test_teardown()
    print("start TEST OK")
    print("TEST OK")
