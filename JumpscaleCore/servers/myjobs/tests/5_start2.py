import gevent


def main(self):

    self.start()

    def wait_2sec():
        gevent.sleep(2)

    for x in range(40):
        self.schedule(wait_2sec)

    gevent.joinall([self.dataloop, self.mainloop])

    self.halt(reset=True)

    print("TEST OK")
