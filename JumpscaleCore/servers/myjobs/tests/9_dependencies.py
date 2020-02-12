from Jumpscale import j

myjobs = j.servers.myjobs

skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/493")
def test_dependencies():
    """
    kosmos -p 'j.servers.myjobs.test("dependencies")'
    """

    myjobs._test_setup()
    assert len(myjobs.workers.find()) == 0

    nrworkers = 3
    myjobs.workers_tmux_start(nrworkers)
    assert len(myjobs.workers.find()) == nrworkers

    def do_ok(process=None, wait_do=0):
        import time

        if wait_do:
            time.sleep(wait_do)
        if process:
            for dep in process.job.dependencies:
                job = process.model_job.get(id=dep)
                assert job.result == "OK"
            return "OK:%s" % job.id
        else:
            return "OK"

    def do_error():
        raise RuntimeError("BOEM")

    job1 = myjobs.schedule(do_ok, wait_do=1)
    job2 = myjobs.schedule(do_ok, wait_do=1)
    job3 = myjobs.schedule(do_ok, dependencies=[job1.id, job2.id], timeout=30, die=True, wait_do=1)

    job3.wait()
    assert job3.state == "OK"

    job1 = myjobs.schedule(do_ok, wait_do=1)
    job2 = myjobs.schedule(do_error)
    job3 = myjobs.schedule(do_ok, wait_do=1, dependencies=[job1.id, job2.id], timeout=10, die=False)

    job3.wait(die=False)
    job2.load()
    # need to wait for job1 might not be done yet
    job1.wait()

    assert job3.state == "ERROR"
    assert job3.error["dependency_failure"] == job2.id
    assert job2.state == "ERROR"
    assert job1.state == "OK"
    myjobs._test_teardown()
    print("TEST OK FOR dependencies")
