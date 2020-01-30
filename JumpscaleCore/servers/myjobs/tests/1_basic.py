from Jumpscale import j

myjob = j.servers.myjobs


def test_basic():
    """
    kosmos -p 'j.servers.myjobs.test("basic")'
    """

    j.tools.logger.debug = True

    j.servers.myjobs._test_setup()

    def add(a=None, b=None):
        assert a
        assert b
        return a + b

    job = j.servers.myjobs.schedule(add, a=1, b=2)
    jobid = job.id
    assert isinstance(jobid, int)

    # means work scheduled)
    assert j.servers.myjobs.scheduled_ids == [jobid]

    assert j.servers.myjobs.jobs

    j.servers.myjobs.worker_inprocess_start()  # will only run 1 time
    assert j.servers.myjobs.scheduled_ids == [jobid]

    job.load()
    assert job.state == "OK"
    assert job.time_start > j.data.time.epoch - 10
    assert job.time_stop > j.data.time.epoch - 10
    assert job.result == 3
    assert job.id == jobid
    assert job.check_ready()

    res = j.servers.myjobs.results()

    assert len(res) == 1
    assert res[0] == 3

    job = j.servers.myjobs.jobs.find()[0]
    assert job.error == {}
    assert job.result == 3
    assert job.state == "OK"
    assert job.time_stop > 0

    job = j.servers.myjobs.schedule(add, a=3, b=4)
    jobid = job.id
    j.servers.myjobs.worker_inprocess_start()

    res = j.servers.myjobs.results([jobid])
    v = [i for i in res]
    assert v[0] == 7

    job = j.servers.myjobs.schedule(add, a=3, b=4)
    j.servers.myjobs.worker_inprocess_start()
    res = job.wait()
    print(res)
    j.servers.myjobs._test_teardown()
    print("Basic TEST OK")
    print("TEST OK")
