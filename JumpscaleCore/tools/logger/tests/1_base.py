from Jumpscale import j


class TestClass(j.baseclasses.object):
    def _init(self, **kwargs):
        self._logger_ = None
        self._log("a message", level=20)

    @property
    def _logger(self):
        if self._logger_ is None:
            # print("LOGGER ATTACH: %s"%self._location)
            self._logger_ = j.tools.logger
        return self._logger_

    def test_basic_log(self, nr):
        for i in range(nr):
            self._log("a message", level=20)

        j.shell()


def main(self):
    """
    to run:

    kosmos 'j.tools.logger.test(name="base")'
    """

    # j.tools.logger.me.redis = False

    # make sure its warm
    e = TestClass()
    e._init()

    def base1():

        ddict = {}
        nr = 10000
        j.tools.timer.start("basic test for %s classes creation with logger", memory=True)
        for i in range(nr):
            ddict[str(i)] = TestClass()
            ddict[str(i)]._init()
        j.tools.timer.stop(nr)

    base1()

    def base2():

        nr = 100000
        j.tools.timer.start("basic test for logging without stdout/redis", memory=True)
        for i in range(nr):
            e._logger._log("a message", level=20)
        j.tools.timer.stop(nr)

    base2()

    # j.tools.logger.me.redis_addr = "127.0.0.1"
    # j.tools.logger.me.redis_port = 6379
    # j.tools.logger.me.redis = True

    def base3():

        nr = 10000
        j.tools.timer.start("basic test for logging with stdout/redis", memory=True)
        for i in range(nr):
            e._logger._log("a message", level=20)
        j.tools.timer.stop(nr)

        # RESULTIS WE CAN +- do +10k logs per sec to redis (this can be improved over local socket for sure)

    base3()
