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


# NOT USED YET
from Jumpscale import j
from .JSBaseConfig import JSBaseConfig

from gevent import queue
from gevent import spawn
from gevent.event import Event


def property_js(func):
    def wrapper_action(*args, **kwargs):
        self = args[0]
        args = args[1:]
        self._log_debug(str(func))
        if self._running is None:
            self.service_manage()
        name = func.__name__
        if skip_for_debug or "noqueue" in kwargs:
            if "noqueue" in kwargs:
                kwargs.pop("noqueue")
            res = func(*args, **kwargs)
            return res
        else:
            event = Event()
            action = self._action_new(name=name, args=args, kwargs=kwargs)
            self.action_queue.put((func, args, kwargs, event, action.id))
            event.wait(1000.0)  # will wait for processing
            res = j.data.serializers.msgpack.loads(action.result)
            self._log_debug("METHOD EXECUTED OK")
            return action

    return wrapper_action


# # PythonDecorators/decorator_function_with_arguments.py
# def decorator_function_with_arguments(arg1, arg2, arg3):
#     def wrap(f):
#         print("Inside wrap()")
#         def wrapped_f(*args):
#             print("Inside wrapped_f()")
#             print("Decorator arguments:", arg1, arg2, arg3)
#             f(*args)
#             print("After f(*args)")
#         return wrapped_f
#     return wrap
#
# def do_once2(*args_,**kwargs_):
#     def wrap(func):
#         print("Inside wrap()")
#         def wrapper_action(*args, **kwargs):
#             j.shell()
#             self=args[0]
#             args=args[1:]
#             name= func.__name__
#
#             if name is not "_init":
#                 self._init()
#             if "reset" in kwargs:
#                 reset = kwargs["reset"]
#             else:
#                 reset = False
#             if not self._done_check(name, reset):
#                 res = func(*args,**kwargs)
#                 self._done_set(name)
#                 return res
#         return wrapper_action
#     return wrap
