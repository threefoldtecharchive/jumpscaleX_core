from Jumpscale import j
import gevent

myjobs = j.servers.myjobs


def test_workers():
    """
    kosmos -p 'j.servers.myjobs.test("workers")'
    """
    myjobs._test_setup()
    j.servers.myjobs.jobs.reset()
    myjobs.workers_subprocess_start(nr_fixed_workers=10)

    j.tools.logger.debug = True

    def add(a=None, b=None):
        assert a
        assert b
        return a + b

    def add_error(a=None, b=None):
        assert a
        assert b
        raise j.exceptions.Base("s")

    def wait_2sec():
        gevent.sleep(3)

    # test the behaviour for 1 job in process, only gevent for data handling
    job_sch = myjobs.schedule(add_error, return_queues=["queue_err"], a=1, b=2)

    myjobs.results(ids=[job_sch.id], return_queues=["queue_err"], die=False)

    job = myjobs.jobs.get(id=job_sch.id)

    assert job.state == "ERROR"

    assert len(job.error.keys()) > 0
    assert job.state == "ERROR"
    assert job.time_stop > 0

    jobs = myjobs.jobs.find()

    assert len(jobs) == 1

    # lets start from scratch, now we know the super basic stuff is working

    ids = []
    for x in range(10):
        job = myjobs.schedule(add, return_queues=["queue_a"], a=1, b=2)
        ids.append(job.id)

    job = j.servers.myjobs.schedule(add_error, return_queues=["queue_a"], return_queues_reset=True, a=1, b=2)
    ids.append(job.id)

    jobs = myjobs.jobs.find()

    # up to now we have 12 jobs total
    assert len(jobs) == 12

    wait_2sec()

    assert myjobs.queue_jobs_start.qsize() == 0  # there need to be 0 jobs in queue (all executed by now)

    for jid in ids[:-1]:
        job = myjobs.jobs.get(id=jid)

        assert job.state == "OK"

        assert len(job.error.keys()) == 0
        assert job.time_stop > 0

    job = myjobs.jobs.get(id=ids[-1])

    assert job.state == "ERROR"
    assert len(job.error.keys()) > 0
    assert job.state == "ERROR"
    assert job.time_stop > 0

    # 3rd test
    ids = []
    for x in range(20):
        job = myjobs.schedule(wait_2sec, return_queues=["queue_b"])
        ids.append(job.id)

    job = j.servers.myjobs.schedule(wait_2sec, return_queues=["queue_b"], timeout=1)
    ids.append(job.id)
    job = j.servers.myjobs.schedule(add_error, return_queues=["queue_b"], a=1, b=2)
    ids.append(job.id)

    print("there should be 10 workers, so wait is max 5 sec")

    gevent.sleep(5)

    # up to now we have 34 jobs in total
    jobs = myjobs.jobs.find()
    assert len(jobs) == 34

    gevent.sleep(5)

    for jid in ids[:-2]:
        job = myjobs.jobs.get(id=jid)

        assert job.state == "OK"

        assert len(job.error.keys()) == 0
        assert job.time_stop > 0

    job = myjobs.jobs.get(id=ids[-2])

    assert job.state == "ERROR"
    assert len(job.error.keys()) > 0
    assert job.state == "ERROR"
    assert job.time_stop > 0

    job = myjobs.jobs.get(id=ids[-1])

    assert job.state == "ERROR"
    assert len(job.error.keys()) > 0
    assert job.state == "ERROR"
    assert job.time_stop > 0

    jobs = myjobs.jobs.find()

    completed = [job for job in jobs if job.time_stop]

    assert len(completed) == 34

    errors = [job for job in jobs if job.error != {}]
    assert len(errors) == 4

    errors = [job for job in jobs if job.state == "ERROR"]
    assert len(errors) == 4

    errors = [job for job in jobs if job.error_cat == "TIMEOUT"]
    assert len(errors) == 1

    jobs = [job for job in jobs if job.state == "OK"]
    assert len(jobs) == 30

    job = j.servers.myjobs.schedule(add_error, return_queues=["queue_a"], return_queues_reset=True, die=True, a=1, b=2)
    try:
        myjobs.results(ids=[job.id], return_queues=["queue_a"], die=True)
        raise AssertionError("Should have died")
    except j.exceptions.Base:
        pass

    print("workers TEST OK")
    print("TEST OK")
