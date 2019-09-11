from Jumpscale import j


def main(self):
    """
    kosmos -p 'j.servers.myjobs.test("basic")'
    """

    j.tools.logger.debug = True

    self.reset()

    def add(a=None, b=None):
        assert a
        assert b
        return a + b

    job = self.schedule(add, a=1, b=2)
    jobid = job.id
    assert isinstance(jobid, int)

    # means work scheduled)
    assert self.scheduled_ids == [jobid]

    assert self.jobs

    self.worker_inprocess_start()  # will only run 1 time
    assert self.scheduled_ids == [jobid]

    job.load()
    assert job.state == "OK"
    assert job.time_start > j.data.time.epoch - 10
    assert job.time_stop > j.data.time.epoch - 10
    assert job.result == 3
    assert job.id == jobid
    assert job.check_ready()

    res = self.results()

    v = [i for i in res.values()]
    assert len(res.values()) == 1
    assert v[0] == 3

    job = self.jobs.find()[0]
    assert job.error == {}
    assert job.result == 3
    assert job.state == "OK"
    assert job.time_stop > 0

    job = self.schedule(add, a=3, b=4)
    jobid = job.id
    self.worker_inprocess_start()

    res = self.results([jobid])
    v = [i for i in res.values()]
    assert v[0] == 7

    job = self.schedule(add, a=3, b=4)
    self.worker_inprocess_start()
    res = job.wait()
    assert res

    self.stop(reset=True)

    print("TEST OK")
