from Jumpscale import j


def main(self, reset=False):
    """
    kosmos -p 'j.servers.myjobs.test("dependencies")'
    kosmos -p 'j.servers.myjobs.test("dependencies",reset=True)'
    """

    if reset:
        self.stop(reset=True)  # will make sure all tmux are gone
        assert len(self.find()) == 0

    nrworkers = 3
    self.workers_tmux_start(nrworkers)
    assert len(self.find()) == nrworkers

    def do_ok(job=None, wait_do=0):
        import time

        if wait_do:
            time.sleep(wait_do)
        if job:
            for dep in job.dependencies:
                job = j.servers.myjobs.model_job.get(dep)
                assert job.result == "OK"
            return "OK:%s" % job.id
        else:
            return "OK"

    def do_error():
        raise RuntimeError("BOEM")

    job1 = self.schedule(do_ok, wait_do=1)
    job2 = self.schedule(do_ok, wait_do=1)
    job3 = self.schedule(do_ok, wait_do=1, dependencies=[job1, job2], timeout=30, die=True)

    job3.wait()
    assert job3.state == "OK"

    job1 = self.schedule(do_ok, wait_do=1)
    job2 = self.schedule(do_error)
    job3 = self.schedule(do_ok, wait_do=1, dependencies=[job1, job2], timeout=10, die=False)

    job2 = self.jobs.get(id=job2.id)
    job1 = self.jobs.get(id=job1.id)

    job3.wait()

    assert job3.state == "ERROR"
    assert job3.error["dependency_failure"] == job2.id
    assert job2.state == "ERROR"
    assert job1.state == "OK"

    print("TEST OK FOR dependencies")

    # j.application.stop()
