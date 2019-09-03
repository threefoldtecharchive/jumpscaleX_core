import gevent


def main(self):
    """
    kosmos -p 'j.servers.myjobs.test("start2")'
    """

    self.workers_subprocess_start()

    def wait_2sec():
        gevent.sleep(2)

    for x in range(40):
        self.schedule(wait_2sec)

    gevent.joinall([self.dataloop, self.mainloop])

    self.stop(reset=True)

    print("TEST OK")
