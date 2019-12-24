from Jumpscale import j
import gevent


def main(self):
    """
    kosmos -p 'j.servers.myjobs.test("timeout")'
    """
    self._test_setup()
    j.tools.logger.debug = True

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
    self._test_teardown()
    print("timeout TEST OK")
    print("TEST OK")
