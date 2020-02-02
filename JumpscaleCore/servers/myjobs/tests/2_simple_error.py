from Jumpscale import j

myjobs = j.servers.myjobs


def test_simple_error():
    """
    kosmos -p 'j.servers.myjobs.test("simple_error")'
    """

    myjobs._test_setup()

    j.tools.logger.debug = True

    def add(a=None, b=None):
        assert a
        assert b
        raise ValueError("aaa")

    job = myjobs.schedule(add, a=1, b=2)

    error = False

    myjobs.worker_inprocess_start()

    ##there should be job in errorstate

    try:
        myjobs.results()
    except Exception as e:
        error = True

    assert error

    job = myjobs.schedule(add, a=1, b=2)
    job_id = job.id

    myjobs._log_info("job id waiting for:%s" % job_id)

    myjobs.worker_inprocess_start()

    jobs = {job.id: job for job in j.servers.myjobs.wait(die=False)}
    jobs[job_id].error["traceback"]

    assert len(jobs[job_id].error["traceback"]) > 0

    print(myjobs.results([job_id], die=False))

    myjobs._log_info("basic error test done")
    print("Simple_error TEST OK")
    print("TEST OK")
