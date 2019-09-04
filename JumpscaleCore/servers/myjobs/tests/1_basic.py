from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.myjobs.test("basic")'
    """

    j.tools.logger.debug = True

    self.reset()

    def add(a, b):
        return a + b

    job = self.schedule(add, 1, 2)
    jobid = job.id
    assert isinstance(jobid, int)

    # means work scheduled
    assert self.scheduled_ids == [jobid]

    self.worker_inprocess_start()
    assert self.scheduled_ids == [jobid]

    res = self.results()

    v = [i for i in res.values()]
    assert len(res.values()) == 1
    assert v[0] == str(3)

    job = self.model_job.find()[0]
    assert job.error == {}
    assert job.result == "3"
    assert job.state == "OK"
    assert job.time_stop > 0

    job = self.schedule(add, 3, 4)
    jobid = job.id
    self.worker_inprocess_start()

    res = self.results([jobid])
    v = [i for i in res.values()]
    assert v[0] == str(7)

    print(res)

    self.stop(reset=False)

    print("TEST OK")
