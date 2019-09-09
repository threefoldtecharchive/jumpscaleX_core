from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.myjobs.test("simple_error")'
    """

    j.tools.logger.debug = True

    self.reset()
    self.start()

    def add(a=None, b=None):
        assert a
        assert b
        raise ValueError("aaa")

    job = self.schedule(add, a=1, b=2)

    error = False

    self.worker_inprocess_start()

    ##there should be job in errorstate

    try:
        res = self.results()
    except Exception as e:
        error = True

    assert error

    job = self.schedule(add, a=1, b=2)
    job_id = job.id

    self._log_info("job id waiting for:%s" % job_id)

    self.worker_inprocess_start()

    res = self.results(die=False)

    res[job_id].error["traceback"]

    assert len(res[job_id].error["traceback"]) > 0

    # print(self.results([job]))

    self._log_info("basic error test done")

    self.stop(reset=False)

    print("TEST OK")
