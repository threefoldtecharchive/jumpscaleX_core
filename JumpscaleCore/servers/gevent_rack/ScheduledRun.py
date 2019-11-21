from Jumpscale import j
from gevent import Greenlet
import gevent
from .ScheduledJob import ScheduledJob


class ScheduledRun(j.baseclasses.object):
    def _init(self, name, timeout=1200):
        self.name = name
        self.jobs = {}
        self.mainloop = Greenlet(self._mainloop)
        self.mainloop.start()
        self.timeout = timeout
        self.error = ""
        self.sleep_time = 0.1
        self.nr_scheduled = 0  # last nr as used for scheduling
        self.nr_done = 0  # nr of last job succesfully executed
        self.events = {}

    def _mainloop(self):
        while True:
            # need to do in careful way so we never kill the greenlet
            self.check()
            gevent.sleep(self.sleep_time)

    # def greenlet_add(self, name, method, *args, **kwargs):
    #     if name in self.greenlets:
    #         raise j.exceptions.BASE("cannot add greenlet: %s already exists" % name)
    #     g = Greenlet(method, *args, **kwargs)
    #     self.greenlets[name] = g
    #     self.greenlets[name].start()

    def schedule(self, name, method, period=0, time_start=0, timeout=0, event=None, retry=None, **kwargs):
        """

        :param self:
        :param name:
        :param method: method to execute
        :param period: recurring period in seconds, 0 means only run once
        :param start_time: time to start in epoch, in <100000 then will do current epoch + this time
        :param timeout: in seconds after start
        :param args:
        :param kwargs:
        :return:
        """
        if time_start < 100000 and time_start != 0:
            time_start = j.data.time.epoch + time_start

        nr = 1
        name_ = name
        while name_ in self.jobs:
            nr += 1
            name_ = name + str(nr)

        name = name_

        self.nr_scheduled += 1
        sj = ScheduledJob(
            name=name,
            method=method,
            args=[],
            kwargs=kwargs,
            period=period,
            time_start=time_start,
            timeout=timeout,
            nr=self.nr_scheduled,
            event=event,
            retry=retry,
        )
        self.jobs[name] = sj

    def check(self):
        now = j.data.time.epoch
        keys = [key for key in self.jobs.keys()]
        for key in keys:
            if key in self.jobs:
                gs = self.jobs[key]
                if gs.event:
                    if self.nr_done < gs.event:
                        # means we cannot start yet
                        continue
                gs.check()

    def event_get(self, name):
        self.events[name] = self.nr_scheduled

    def stop(self):
        self.mainloop.kill()
