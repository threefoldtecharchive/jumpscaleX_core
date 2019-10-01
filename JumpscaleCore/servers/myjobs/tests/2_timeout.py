from Jumpscale import j
import gevent


def main(self):
    """
    kosmos -p 'j.servers.myjobs.test("timeout")'
    """

    j.tools.logger.debug = True

    self.reset()

    def add(a=None, b=None):
        gevent.sleep(2)
        assert a
        assert b
        return a + b

    job = self.schedule(add, a=1, b=2, timeout=1)

    self.worker_inprocess_start()
    job = self.wait([job.id], die=False)[0]
    assert job.state == "ERROR"
    assert job.error_cat == "TIMEOUT"

    self.stop(reset=False)

    print("TEST OK")
