from Jumpscale import j
from gevent import Greenlet


class ScheduledJob(j.baseclasses.object):
    def _init(
        self, name, method, args, kwargs, period=None, time_start=None, timeout=1200, nr=None, event=None, retry=None
    ):
        self.name = name
        self.method = method
        self.args = args
        self.kwargs = kwargs
        if not time_start:
            time_start = j.data.time.epoch
        self.time_start = time_start
        self.time_started = 0
        self.time_stopped_last = 0
        self.period = period
        self.greenlet = None
        self.timeout = timeout
        self.error = None
        self.nr = nr
        self.event = event  # is the nr we need to wait for in our scheduling job
        self.result = None
        self.retry = retry
        self.done = False

    def check(self):
        """
        check if the job is running well, if there was timeout or error
        :return:
        """
        now = j.data.time.epoch

        if self.done:
            return
        if self.greenlet:
            if self.timeout:
                self._log_debug("timeout:%s" % self.name)
                if self.time_start + self.timeout > now:
                    self.raise_error("timeout")
                    return self._stop()
            if self.greenlet.exception:
                self._log_debug("exception:%s" % self.name)
                # error happened in the greelet
                self.raise_error()
                return self._stop()
            if self.greenlet.successful():
                j.shell()
                self._log_debug("ok:%s" % self.name)
                self.error = None
                self.result = self.greenlet.value
                return self._stop()
            if self.greenlet.dead:
                self._log_debug("dead:%s" % self.name)

            self._log_debug("running:%s" % self.name)
        else:
            if self.time_start < now:
                self._log_debug("start:%s" % self.name)
                self.run()

    def create(self):
        """
        create the greenlet
        :param self:
        :return:
        """
        if self.greenlet:
            return self.raise_error("cannot run, is already running")
        self.greenlet = Greenlet(self.method, *self.args, **self.kwargs)

    def run(self):
        if not self.greenlet:
            self.create()
        self.greenlet.start()
        self.time_started = j.data.time.epoch

    def _stop(self):
        self.time_stopped_last = j.data.time.epoch
        self.greenlet.kill()
        # remove greenlet
        self.greenlet = None
        if self.error and self.retry and self.retry > 0:
            self.retry -= 1
            self.time_start = j.data.time.epoch
        elif self.period:
            self.time_start = j.data.time.epoch + self.period
        else:
            self.time_start = None
            self.done = True

    def raise_error(self, msg=None):
        if not msg:
            # TODO:get error info from greenlet
            j.shell()
        self.error = msg
