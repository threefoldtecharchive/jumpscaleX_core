from Jumpscale import j
import gevent


def main(self):
    """
    kosmos -p 'j.servers.myjobs.test("workers")'
    """

    j.tools.logger.debug = True

    self.stop(reset=True)

    def reset():
        # kill leftovers from last time, if any
        self.reset()

        jobs = self.jobs.find()
        assert len(jobs) == 0
        assert self.queue_jobs_start.qsize() == 0

        self._workers_gipc_nr_max = 10
        self.workers_subprocess_start()

    def add(a=None, b=None):
        assert a
        assert b
        return a + b

    def add_error(a=None, b=None):
        import time

        assert a
        assert b
        raise j.exceptions.Base("s")

    def wait_2sec():
        gevent.sleep(3)

    reset()

    # test the behaviour for 1 job in process, only gevent for data handling
    job_sch = self.schedule(add_error, a=1, b=2)

    job_sch.wait(die=False)
    jobid = job_sch.id

    assert job_sch.state == "ERROR"

    job = self.jobs.get(id=jobid)

    assert len(job.error.keys()) > 0
    assert job.state == "ERROR"
    assert job.time_stop > 0

    jobs = self.jobs.find()

    assert len(jobs) == 1
    job = jobs[0]
    assert len(job.error.keys()) > 0
    assert job.state == "ERROR"
    assert job.time_stop > 0

    # lets start from scratch, now we know the super basic stuff is working

    reset()

    for x in range(10):
        self.schedule(add, a=1, b=2)

    errorjob = j.servers.myjobs.schedule(add_error, a=1, b=2)

    jobs = self.jobs.find()

    assert len(jobs) == 11

    wait_2sec()

    assert self.queue_jobs_start.qsize() == 0  # there need to be 0 jobs in queue (all executed by now)

    # nothing got started yet
    job = jobs[0]

    res = self.results([job.id])

    assert res == {job.id: 3}  # is the result back

    print("will wait for results")
    assert self.results([jobs[2].id, jobs[3].id, jobs[4].id], timeout=1) == {
        jobs[2].id: 3,
        jobs[3].id: 3,
        jobs[4].id: 3,
    }

    self.wait([errorjob.id], die=False)
    jobs = self.jobs.find()
    errors = [job for job in jobs if job.state == "ERROR"]
    assert len(errors) == 1

    reset()

    for x in range(20):
        self.schedule(wait_2sec)

    j.servers.myjobs.schedule(wait_2sec, timeout=1)
    j.servers.myjobs.schedule(add_error, a=1, b=2)

    print("there should be 10 workers, so wait is max 5 sec")

    jobs = self.jobs.find()
    assert len(jobs) == 22

    gevent.sleep(5)

    completed = [job for job in jobs if job.time_stop]

    assert len(completed) == 22

    errors = [job for job in jobs if job.error != {}]
    assert len(errors) == 2

    errors = [job for job in jobs if job.state == "ERROR"]
    assert len(errors) == 2

    errors = [job for job in jobs if job.error_cat == "TIMEOUT"]
    assert len(errors) == 1

    jobs = [job for job in jobs if job.state == "OK"]
    assert len(jobs) == 20

    self.stop(reset=True)

    print("workers TEST OK")
    print("TEST OK")
