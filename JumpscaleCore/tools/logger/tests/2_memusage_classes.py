from Jumpscale import j


class TestClass(j.baseclasses.object):
    def _init(self, **kwargs):
        # self._logger  # triggers logger
        pass

    def test_basic_log(self, nr):
        for i in range(nr):
            self._log("a message", level=20)

        j.shell()


def main(self):
    """
    to run:

    kosmos 'j.tools.logger.test(name="memusage_classes")'

    conclusion:
        base classes do not use that much mem
        30MB for 100.000 classes which become objects in mem

    """

    ddict = {}
    nr = 100000
    j.tools.timer.start("basic test for %s logs" % nr, memory=True)
    for i in range(nr):
        ddict[str(i)] = TestClass()
    j.tools.timer.stop(nr)
