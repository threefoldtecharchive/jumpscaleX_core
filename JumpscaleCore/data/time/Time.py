import datetime
import time
from .TimeInterval import TimeInterval
from Jumpscale import j
import struct

TIMES = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 3600 * 24,
    "w": 3600 * 24 * 7,
    "M": int(3600 * 24 * 365 / 12),
    "Y": 3600 * 24 * 365,
}


class Time_(object):
    """
    generic provider of time functions
    lives at j.data.time
    """

    __jslocation__ = "j.data.time"

    def __init__(self):
        self.timeinterval = TimeInterval()

    @property
    def epoch(self):
        """
        j.data.time.epoch
        """

        return int(time.time())

    def getTimeEpoch(self):
        """
        Get epoch timestamp (number of seconds passed since January 1, 1970)
        """
        timestamp = int(time.time())
        return timestamp

    def getSecondsInHR(self, seconds):
        """
        j.data.time.getSecondsInHR(365)
        """
        minute = 60.0
        hour = 3600.0
        day = hour * 24
        week = day * 7
        if seconds < minute:
            return "%s seconds" % seconds
        elif seconds < hour:
            return "%s minutes" % round((seconds / minute), 1)
        elif seconds < day:
            return "%s hours" % round((seconds / hour), 1)
        elif seconds < week:
            return "%s days" % round((seconds / day), 1)
        else:
            return "%s weeks" % round((seconds / week), 1)

    def getTimeEpochBin(self):
        """
        Get epoch timestamp (number of seconds passed since January 1, 1970) in binary format of 4 bytes
        """
        return struct.pack("<I", self.getTimeEpoch())

    def getLocalTimeHR(self):
        """
        Get the current local date and time in a human-readable form

        j.data.time.getLocalTimeHR()
        """
        # timestamp = time.asctime(time.localtime(time.time()))
        timestr = self.formatTime(self.getTimeEpoch())
        return timestr

    def getLocalTimeHRForFilesystem(self):
        # TODO: check if correct implementation
        return time.strftime("%d_%b_%Y_%H_%M_%S", time.gmtime())

    def formatTime(self, epoch, formatstr="%Y/%m/%d %H:%M:%S", local=True):
        """
        Returns a formatted time string representing the current time

        See http://docs.python.org/lib/module-time.html#l2h-2826 for an
        overview of available formatting options.

        @param format: Format string
        @type format: string

        @returns: Formatted current time
        @rtype: string
        """
        epoch = float(epoch)
        if local:
            timetuple = time.localtime(epoch)
        else:
            timetuple = time.gmtime(epoch)
        timestr = time.strftime(formatstr, timetuple)
        return timestr

    def epoch2HRDate(self, epoch, local=True):
        return self.formatTime(epoch, "%Y/%m/%d", local)

    def epoch2HRDateTime(self, epoch, local=True):
        return self.formatTime(epoch, "%Y/%m/%d %H:%M:%S", local)

    def pythonDateTime2HRDateTime(self, pythonDateTime, local=True):
        if not isinstance(pythonDateTime, datetime.datetime):
            raise j.exceptions.Input("needs to be python date.time obj:%s" % pythonDateTime)
        epoch = pythonDateTime.timestamp()
        return self.epoch2HRDateTime(epoch)

    def pythonDateTime2Epoch(self, pythonDateTime, local=True):
        if not isinstance(pythonDateTime, datetime.datetime):
            raise j.exceptions.Input("needs to be python date.time obj:%s" % pythonDateTime)

        epoch = pythonDateTime.timestamp()
        return epoch

    def epoch2pythonDateTime(self, epoch):
        return datetime.datetime.fromtimestamp(epoch)

    def epoch2ISODateTime(self, epoch):
        dt = datetime.datetime.fromtimestamp(epoch)
        return dt.isoformat()

    def epoch2pythonDate(self, epoch):
        return datetime.date.fromtimestamp(epoch)

    def epoch2HRTime(self, epoch, local=True):
        return self.formatTime(epoch, "%H:%M:%S", local)

    def getMinuteId(self, epoch=None):
        """
        is # min from jan 1 2010
        """
        if epoch is None:
            epoch = time.time()
        if epoch < 1262318400.0:
            raise j.exceptions.Runtime("epoch cannot be smaller than 1262318400, given epoch:%s" % epoch)

        return int((epoch - 1262318400.0) / 60.0)

    def getHourId(self, epoch=None):
        """
        is # hour from jan 1 2010
        """
        return int(self.getMinuteId(epoch) / 60)

    def fiveMinuteIdToEpoch(self, fiveMinuteId):
        return fiveMinuteId * 60 * 5 + 1262318400

    def get5MinuteId(self, epoch=None):
        """
        is # 5 min from jan 1 2010
        """
        return int(self.getMinuteId(epoch) / 5)

    def getDayId(self, epoch=None):
        """
        is # day from jan 1 2010
        """
        return int(self.getMinuteId(epoch) / (60 * 24))

    def getDeltaTime(self, txt):
        """
        only supported now is -3m, -3d and -3h (ofcourse 3 can be any int)
        and an int which would be just be returned
        means 3 days ago 3 hours ago
        if 0 or '' then is now
        """
        txt = txt.strip()
        unit = txt[-1]
        if txt[-1] not in list(TIMES.keys()):
            raise j.exceptions.Runtime(
                "Cannot find time, needs to be in format have time indicator %s " % list(TIMES.keys())
            )
        value = float(txt[:-1])
        return int(value * TIMES[unit])

    def getEpochDeltaTime(self, txt):
        """
        only supported now is + and -3m, -3d and -3h  (ofcourse 3 can be any int)
        and an int which would be just be returned
        means 3 days ago 3 hours ago
        if 0 or '' then is now

        supported:

            s (second) ,m (min) ,h (hour) ,d (day),w (week), M (month), Y (year)

        """
        if txt is None or str(txt).strip() == "0":
            return self.getTimeEpoch()
        return self.getTimeEpoch() + self.getDeltaTime(txt)

    def HRDateToEpoch(self, datestr, local=True):
        """
        convert string date to epoch
        Date needs to be formatted as 1988/06/16  (Y/m/d)
        """
        if datestr.strip() == "":
            return 0
        try:
            datestr = datestr.strip()
            return time.mktime(time.strptime(datestr, "%Y/%m/%d"))
        except BaseException:
            raise j.exceptions.Value(
                'Date needs to be formatted as " 1988/06/16", also check if date is valid, now format = %s' % datestr
            )

    def HRDateTime2epoch(self, hrdatetime):
        """
        convert string date/time to epoch
        Needs to be formatted as 16/06/1988 %H:%M:%S
        """
        if hrdatetime.strip() == "":
            return 0
        try:
            hrdatetime = hrdatetime.strip()
            return int(time.mktime(time.strptime(hrdatetime, "%Y/%m/%d %H:%M:%S")))
        except BaseException:
            raise j.exceptions.Value(
                "Date needs to be formatted as Needs to be formatted as 16/06/1988 %H:%M:%S, also check if date is valid, now format = %s"
                % hrdatetime
            )

    def any2epoch(self, val, in_list=False):
        """
        if list will go item by item until not empty,0 or None
        if int is epoch
        if string is human readable format
        if date.time yeh ...
        """
        if j.data.types.list.check(val):
            for item in val:
                res = self.any2epoch(item, in_list=True)
                if res != 0:
                    return res
            return 0
        if val is None:
            return 0
        if j.data.types.int.check(val):
            return val
        if j.data.types.string.check(val):
            try:
                return self.HRDateTime2epoch(val)
            except BaseException:
                pass
            try:
                return self.HRDatetoEpoch(val)
            except BaseException:
                pass
        if isinstance(val, datetime.datetime):
            return self.pythonDateTime2Epoch(val)
        if not in_list:
            raise j.exceptions.Input(
                "Could not define format of time value, needs to be int, human readable time, list or python datetime obj."
            )
        else:
            return 0

    def any2HRDateTime(self, val):
        """
        if list will go item by item until not empty,0 or None
        if int is epoch
        if string is human readable format
        if date.time yeh ...
        """
        epoch = self.any2epoch(val)
        return self.epoch2HRDateTime(epoch)

    def test(self):
        now = self.getTimeEpoch()
        hr = self.epoch2HRDateTime(now)
        assert self.HRDateTime2epoch(hr) == now
        assert self.any2epoch(hr) == now
        dt = self.epoch2pythonDateTime(now)
        assert self.any2epoch(dt) == now
        hr = self.pythonDateTime2HRDateTime(dt)
        assert self.any2epoch(hr) == now
        hr = self.any2HRDateTime(now)
        assert self.any2epoch(hr) == now
        hr = self.any2HRDateTime(hr)
        assert self.any2epoch(hr) == now
        hr = self.any2HRDateTime(dt)
        assert self.any2epoch(hr) == now
        hr = self.any2HRDateTime(["", 0, dt])
        assert self.any2epoch(hr) == now
