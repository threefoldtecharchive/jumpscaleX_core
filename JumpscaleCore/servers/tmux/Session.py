from Jumpscale import j
import time
import libtmux as tmuxp
import os

JSBASE = j.baseclasses.object

# from .Pane import Pane
from .Window import Window


class Session(j.baseclasses.object):
    def __init__(self, session):
        JSBASE.__init__(self)
        self.id = session.get("session_id")
        self.name = session.get("session_name")
        self.mgmt = session
        self._windows = []

    @property
    def windows(self):
        self._windows = []
        for w in self.mgmt.list_windows():
            self._windows.append(Window(self, w))
        return self._windows

    def window_remove(self, name):
        windows = self.mgmt.list_windows()
        if len(windows) < 2:
            self.window_get(name="ignore", removeIgnore=False)
        for w in self.mgmt.windows:
            wname = w.get("window_name")
            if name == wname:
                w.kill_window()

    def window_exists(self, name):
        for window in self.windows:
            if window.name == name:
                return True
        return False

    def window_get(self, name, start_directory=None, attach=False, reset=False, removeIgnore=True):

        # from pudb import set_trace; set_trace()
        if reset:
            self.window_remove(name)

        for window in self.windows:
            if window.name == name:
                # is right construct, means we found a window, now we can safely remove ignore
                if self.window_exists("ignore") and removeIgnore:
                    self.window_remove("ignore")
                return window

        self._log_debug("create window:%s" % name)
        res = self.mgmt.new_window(name, start_directory=start_directory, attach=attach)

        window = Window(self, res)
        self.windows.append(window)
        if attach:
            window.select()

        # when only 1 pane then ignore had to be created again
        if self.window_exists("ignore") and removeIgnore:
            self.window_remove("ignore")

        return window

    def kill(self):
        for window in self.windows:
            window.kill()

    def __repr__(self):
        return "session:%s:%s" % (self.id, self.name)

    __str__ = __repr__
