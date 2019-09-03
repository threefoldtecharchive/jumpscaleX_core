import gevent

from Jumpscale import j

import time


def main(self):
    """
    kosmos -p 'j.servers.myjobs.test("dependencies")'
    """

    self.stop(reset=True)  # will make sure all tmux are gone
    assert len(self.find()) == 0

    self.workers_tmux_start(4)

    assert len(self.find()) == 4

    def do_ok(job=None, wait=0):
        if wait:
            time.sleep(wait)
        if job:
            for dep in job.dependencies:
                j.shell()
                w
            return "OK:%s" % job.id
        else:
            return "OK"

    def do_ok(nr=None, job=None):
        return "OK:%s" % nr

    def do_error():
        raise RuntimeError("BOEM")

    job1 = self.schedule(do_ok, wait=4)
    job2 = self.schedule(do_ok, wait=2)
    job3 = self.schedule(do_ok, dependencies=[job1, job2], wait=True)

    print("TEST OK FOR dependencies")
