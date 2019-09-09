from Jumpscale import j
import gevent


def main(self):
    """
    kosmos -p 'j.servers.myjobs.test("workers")'
    """

    j.tools.logger.debug = True

    j.tools.logger.debug = True

    def reset():
        # kill leftovers from last time, if any
        self.reset()
        # self.init()

        jobs = self.model_job.find()
        assert len(jobs) == 0
        assert self.queue_jobs_start.qsize() == 0
        assert self.queue_return.qsize() == 0

    def add(a=None, b=None):
        assert a
        assert b
        return a + b

    def add_error(a=None, b=None):
        assert a
        assert b
        raise j.exceptions.Base("s")

    def wait_2sec():
        gevent.sleep(2)

    reset()

    self.workers_tmux_start(4)

    # test the behaviour for 1 job in process, only gevent for data handling
    job_sch = self.schedule(add_error, a=1, b=2)
    jobid = job_sch.id
    wait_2sec()

    job = self.model_job.get(jobid)

    assert len(job.error.keys()) > 0
    assert job.result == ""
    assert job.state == "ERROR"
    assert job.time_stop > 0

    jobs = self.model_job.find()

    assert len(jobs) == 1
    job = jobs[0]
    assert len(job.error.keys()) > 0
    assert job.result == ""
    assert job.state == "ERROR"
    assert job.time_stop > 0

    # lets start from scratch, now we know the super basic stuff is working
    reset()
    self.workers_tmux_start(4)

    for x in range(10):
        self.schedule(add, a=1, b=2)

    j.servers.myjobs.schedule(add_error, a=1, b=2)

    jobs = self.model_job.find()

    assert len(jobs) == 11

    wait_2sec()
    assert self.queue_jobs_start.qsize() == 0  # there need to be 0 jobs in queue (all executed by now)

    # nothing got started yet

    gevent.spawn(self._data_loop)

    job = jobs[0]

    res = self.results([job.id])

    assert res == {job.id: "3"}  # is the result back

    assert 3 == j.servers.myjobs.schedule(add, a=1, b=2, inprocess=True)

    print("will wait for results")
    assert self.results([jobs[2].id, jobs[3].id, jobs[4].id], timeout=1) == {
        jobs[2].id: "3",
        jobs[3].id: "3",
        jobs[4].id: "3",
    }

    jobs = self.model_job.find()
    errors = [job for job in jobs if job.state == "ERROR"]
    assert len(errors) == 1

    # test with publish_subscribe channels
    queue_name = "myself"
    q = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % queue_name)
    q.reset()  # lets make sure its empty

    j.servers.myjobs.schedule(add, a=1, b=2, return_queues=[queue_name])
    gevent.sleep(0.5)
    assert q.qsize() == 1
    # job_return = j.servers.myjobs.wait("myself")
    # assert job_return.result == "3"
    # assert job_return.id == 11
    # assert job_return.state == "OK"

    # TMUX and in process tests are done, lets now see if as subprocess it works

    reset()
    self.workers_tmux_start(nr_workers=10)

    print("wait to schedule jobs")
    gevent.sleep(2)

    for x in range(20):
        self.schedule(wait_2sec)

    j.servers.myjobs.schedule(wait_2sec, timeout=1)
    j.servers.myjobs.schedule(add_error, a=1, b=2)

    print("there should be 10 workers, so wait is max 5 sec")
    gevent.sleep(10)

    # now timeout should have happened & all should have executed

    jobs = self.model_job.find()

    assert len(jobs) == 22

    completed = [job for job in jobs if job.time_stop]

    assert len(completed) == 21

    errors = [job for job in jobs if job.error != {}]
    assert len(errors) == 2

    errors = [job for job in jobs if job.state == "ERROR"]
    assert len(errors) == 2

    # errors = [job for job in jobs if job.error == "TIMEOUT"]
    # assert len(errors) == 1

    jobs = [job for job in jobs if job.state == "OK"]
    assert len(jobs) == 20

    self.stop(reset=True)

    print("TEST OK")
