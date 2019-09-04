from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.myjobs.test("simple_error")'
    """
    self.stop(reset=True)

    j.tools.logger.debug = True

    self.reset()

    def add(a, b):
        raise ValueError("aaa")

    job = self.schedule(add, 1, 2)

    error = False

    self.worker_inprocess_start()

    ##there should be job in errorstate

    try:
        res = self.results()
    except Exception as e:
        error = True

    assert error

    job = self.schedule(add, 1, 2)
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
