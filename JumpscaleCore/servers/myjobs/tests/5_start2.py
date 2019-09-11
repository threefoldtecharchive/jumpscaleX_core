import gevent


def main(self, count=40):
    """
    kosmos -p 'j.servers.myjobs.test("start2")'
    """

    self.workers_subprocess_start()

    def wait_2sec():
        gevent.sleep(2)

    for x in range(count):
        self.schedule(wait_2sec)

    self.stop(reset=True)
    assert self._mainloop_gipc.ready()

    print("TEST OK")
