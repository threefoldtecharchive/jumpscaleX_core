from Jumpscale import j
import time
import libtmux as tmuxp
import os

JSBASE = j.baseclasses.object

from .Pane import Pane


class Window(j.baseclasses.object):
    def __init__(self, session, window):
        JSBASE.__init__(self)
        self.name = window.get("window_name")
        self.session = session
        self.mgmt = window
        self._panes = []
        self.id = window.get("window_id")

    def reload(self):
        self._panes = []

    @property
    def panes(self):
        if self._panes == []:
            if len(self.mgmt.panes) == 1:
                self._panes = [Pane(self, self.mgmt.panes[0])]
            else:
                for pane in self.mgmt.panes:
                    self._panes.append(Pane(self, pane))
        return self._panes

    def pane_exists(self, name="", id=0):
        """
       if there is only 1 and name is not same then name will be set
        """
        for pane in self.panes:
            if pane.name == name:
                return True
            if pane.id == id:
                return True
        return False

    def pane_get(self, name, killothers=False, reset=False, clear=False):
        """

        :param pane:name of the pane
        :param killothers: will remove all other panes
        :param reset: will reset the pane & restart
        :param clear: will clear (send command clear), only works if no cmd working yet
        :return:
        """

        def get_name(name):
            if name.find("__") != -1:
                name, ext = name.split("__", 1)
            return name

        if len(self.panes) == 1:
            if reset:
                self.panes[0].kill()
            self.panes[0].name_set(name)
            return self.panes[0]
            if clear:
                self.panes[0].mgmt.send_keys("clear")
            return self.panes[0]
        for pane in self.panes:

            if pane.name == name or get_name(pane.name) == name:
                if killothers:
                    for pane2 in self.panes:
                        if pane2.name != name and get_name(pane.name) != name:
                            pane2.kill()
                if reset:
                    pane.kill()
                else:
                    if clear:
                        pane.clear()

                return pane
        raise j.exceptions.RuntimeError("Could not find pane:%s.%s" % (self.name, name))

    def select(self):
        self.mgmt.select_window()

    def kill(self):
        for pane in self.panes:
            pane.kill()
        # if len(self.session.windows.keys()) < 2:
        #     self.session.window_get(name="ignore")
        # self._log_debug("KILL %s" % self.name)
        try:
            self.mgmt.kill_window()
        except:
            pass
        self._panes = []

    def __repr__(self):
        return "window:%s:%s" % (self.id, self.name)

    __str__ = __repr__
