# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


from gevent.event import Event
from Jumpscale import j

# will make sure that every decorated method get's execute one after the other

skip_for_debug = True


def queue_method(func):
    def wrapper_queue_method(*args, **kwargs):
        self = args[0]
        if self.bcdb.dataprocessor_greenlet is None:
            self.bcdb.dataprocessor_start()
        # self._log_debug(str(func))
        if skip_for_debug or "noqueue" in kwargs:
            if "noqueue" in kwargs:
                kwargs.pop("noqueue")
            res = func(*args, **kwargs)
            return res
        else:
            event = Event()
            # print("need to find bcdb through self")
            j.data.bcdb.latest.queue.put((func, args, kwargs, event, None))
            event.wait(1000.0)  # will wait for processing
            # self._log_debug("OK")
            return

    return wrapper_queue_method


def queue_method_results(func):
    def wrapper_queue_method(*args, **kwargs):
        self = args[0]
        if self.bcdb.dataprocessor_greenlet is None:
            self.bcdb.dataprocessor_start()
        # self._log_debug(str(func))
        if skip_for_debug or "noqueue" in kwargs:
            if "noqueue" in kwargs:
                kwargs.pop("noqueue")
            res = func(*args, **kwargs)
            return res
        else:
            event = Event()
            id = j.data.bcdb.latest.results_id + 1  # +1 makes we have copy
            if id == 100000:
                id = 0
                self.results_id = 0
            # print("need to find bcdb through self")
            j.data.bcdb.latest.results_id += 1
            j.data.bcdb.latest.queue.put((func, args, kwargs, event, id))
            event.wait(1000.0)  # will wait for processing
            # self._log_debug("OK")
            res = j.data.bcdb.latest.results[id]
            j.data.bcdb.latest.results.pop(id)
            return res

    return wrapper_queue_method
