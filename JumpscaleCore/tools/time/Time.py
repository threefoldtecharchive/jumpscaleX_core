import calendar
import time

from datetime import datetime
from Jumpscale import j

JSBASE = j.baseclasses.object


class Time(j.baseclasses.object):
    __jslocation__ = "j.tools.time"

    @staticmethod
    def extend(date, months):
        expiry = datetime.fromtimestamp(date)
        month = expiry.month - 1 + months
        year = expiry.year + month // 12
        month = month % 12 + 1
        day = min(expiry.day, calendar.monthrange(year, month)[1])
        extended = datetime(year, month, day, expiry.hour, expiry.minute, expiry.second)
        return int(time.mktime(extended.timetuple()))

    def test(self):
        """
        js_shell 'j.tools.time.test()'
        """
        from_date = datetime(2018, 1, 31, 12, 50, 1, 1)

        # test extending 5 months and 30 days months
        to_date = self.extend(time.mktime(from_date.utctimetuple()), 5)
        to_date = datetime.fromtimestamp(to_date)

        assert to_date.month == 6
        assert to_date.day == 30
        assert to_date.year == 2018
        assert to_date.hour == from_date.hour
        assert to_date.minute == from_date.minute
        assert to_date.second == from_date.second

        # test extending 12 months
        to_date = self.extend(time.mktime(from_date.utctimetuple()), 12)
        to_date = datetime.fromtimestamp(to_date)

        assert to_date.month == 1
        assert to_date.day == 31
        assert to_date.year == 2019
        assert to_date.hour == from_date.hour
        assert to_date.minute == from_date.minute
        assert to_date.second == from_date.second

        # test extending 13 months and february 28 days
        to_date = self.extend(time.mktime(from_date.utctimetuple()), 13)
        to_date = datetime.fromtimestamp(to_date)

        assert to_date.month == 2
        assert to_date.day == 28
        assert to_date.year == 2019
        assert to_date.hour == from_date.hour
        assert to_date.minute == from_date.minute
        assert to_date.second == from_date.second

        # test extending 25 months
        to_date = self.extend(time.mktime(from_date.utctimetuple()), 25)
        to_date = datetime.fromtimestamp(to_date)

        assert to_date.month == 2
        assert to_date.day == 29
        assert to_date.year == 2020
        assert to_date.hour == from_date.hour
        assert to_date.minute == from_date.minute
        assert to_date.second == from_date.second
