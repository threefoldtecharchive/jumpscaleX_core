from Jumpscale import j


def main(self):
    """
    kosmos 'j.servers.myjobs.test("simple_error")'
    """

    j.tools.logger.debug = True

    self.reset()

    def add(a, b):
        raise ValueError("aaa")

    job = self.schedule(add, 1, 2)

    error = False
    self.worker_start(onetime=True)

    ##there should be job in errorstate

    try:
        res = self.results()
    except Exception as e:
        error = True

    assert error

    job_id = self.schedule(add, 1, 2)

    self._log_info("job id waiting for:%s" % job_id)

    self.worker_start(onetime=True)

    res = self.results(die=False)

    res[job_id].error["traceback"]

    assert len(res[job_id].error["traceback"]) > 0

    # print(self.results([job]))

    self._log_info("basic error test done")

    self.halt(reset=True)

    print("TEST OK")
