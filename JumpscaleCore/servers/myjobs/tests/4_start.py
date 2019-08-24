import gevent


def main(self, count=100):
    def wait_1sec():
        gevent.sleep(1)
        return "OK"

    ids = []
    for x in range(count):
        ids.append(self.schedule(wait_1sec))

    self.workers_nr_max = 100
    self.start(subprocess=True)

    res = self.results(ids, timeout=120)

    print(res)

    print("TEST OK")
