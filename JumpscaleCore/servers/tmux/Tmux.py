from .Session import Session
from Jumpscale import j
import libtmux as tmuxp
import time
import psutil

JSBASE = j.baseclasses.object


class Tmux(j.baseclasses.object):
    __jslocation__ = "j.servers.tmux"

    def _init(self, **kwargs):
        self._server = None
        self._session = None
        self._windows_active = {}

    @property
    def session(self):
        """
        Always returns session `main`
        :return:
        """
        if self._session is None:
            session = self.server.find_where({"session_name": "main"})
            self._session = Session(session=session)
        return self._session

    def _find_procs_by_name(self, name, startswith_is_ok=True):
        "Return a list of processes matching 'name'."
        ls = []
        for p in psutil.process_iter(attrs=["name"]):
            # print(p.info['name'])
            if p.info["name"] is None:
                if p.status() == "zombie":
                    j.sal.process.kill(p.pid)
                    continue
            if startswith_is_ok:
                if p.info["name"].startswith(name):
                    ls.append(p)
            else:
                if p.info["name"] == name:
                    ls.append(p)
        return ls

    @property
    def server(self):
        def start():
            cmd = "/sandbox/bin/js_mux start"
            j.sal.process.execute(cmd, die=True)
            time.sleep(0.1)

        if self._server is None:
            self._server = tmuxp.Server()

        if not self._server.has_session("main"):
            start()
            self._log_info("tmux server is running")

        return self._server

    def kill(self):
        """
        kosmos 'j.servers.tmux.kill()'
        """
        self.session.kill()

    def pane_get(self, window="main", pane="main", reset=False):
        w = self.window_get(window=window)
        return w.pane_get(name=pane, killothers=False, reset=reset)

    def window_get(self, window="main", reset=False):
        s = self.session
        return s.window_get(window, reset=reset)

    def window_kill(self, window="main"):
        s = self.session
        w = s.window_get(window)
        w.kill()

    def execute(self, cmd, window="main", pane="main", reset=True):
        """
        """
        p = self.pane_get(window=window, pane=pane, reset=reset)
        p.execute(cmd)
        return p

    def cmd_get(
        self,
        name,
        window_name=None,
        pane_name="main",
        cmd="",
        path=None,
        timeout=30,
        env={},
        ports=[],
        cmd_stop=None,
        process_strings=[],
    ):
        """

        example
        ```
        env={}
        env["color"]="blue"
        cmd = j.servers.tmux.cmd_get(name="test",pane="p21",cmd_start="ls /", env=env,stopcmd="killall...",process_strings=[])
        cmd.stop()
        cmd.start()
        ```


        :param name: name of the command
        :param window: window to use std multi, if None then use windowname as name
        :param pane: pane in the window, make sure there is no overlap e.g. p11
        :param cmd: command to execute in the pane
        :param path: path where to execute
        :param env: are the arguments wich will become env arguments, useful to pass variable to process
        :param ports: array of ports this process will use
        :param stopcmd: if specific command to use to stop a process
        :param process_strings: which strings to check if the process is running
        :return:
        """
        if not window_name:
            window_name = name
        if not self.session.window_exists(window_name):
            window = self.window_get(window=window_name, reset=True)
        else:
            window = self.window_get(window=window_name)

        pane = window.pane_get(pane_name)

        startup_cmd = j.servers.startupcmd.get(
            name=name,
            cmd_start=cmd,
            path=path,
            timeout=timeout,
            env=env,
            ports=ports,
            cmd_stop=cmd_stop,
            process_strings=process_strings,
        )

        startup_cmd._pane_ = pane

        return startup_cmd

    def panes_2x2_get(self, window_name="multi", reset=True):
        """

        :param window_name:
        :param reset:
        :return: (p11,p12,p21,p22) are 4 panes
        """

        window = self.window_get(window_name, reset=reset)

        if len(window.panes) == 4 and reset is False:
            p11 = window.pane_get(name="p11")
            p12 = window.pane_get(name="p12")
            p21 = window.pane_get(name="p21")
            p22 = window.pane_get(name="p22")

        else:
            # xy notation
            p11 = window.pane_get(name="p11", killothers=True)
            p12 = p11.splitVertical("p12")
            p21 = p11.splitHorizontal("p21")
            p22 = p12.splitHorizontal("p22")

        return p11, p12, p21, p22

    def window_digitalme_get(self, window_name="digitalme", reset=True):

        window = self.window_get(window_name, reset=reset)

        if len(window.panes) == 6 and reset is False:
            return window
        else:
            # xy notation
            p11 = window.pane_get(name="p11", killothers=True)
            p13 = p11.splitVertical("p13")
            p21 = p11.splitHorizontal("p21")
            p22 = p13.splitHorizontal("p22")

            p12 = p11.splitVertical("p12")
            p14 = p13.splitVertical("p14")

            return window

    def window_multi_get(self, window_name="multi", reset=False):
        """

        kosmos 'j.servers.tmux.window_multi_get()'

        :param window_name:
        :param reset:
        :return:
        """

        window = self.window_get(window_name, reset=reset)

        if len(window.panes) == 13 and reset is False:
            return window

        p11, p13, p31, p33 = self.panes_2x2_get(window_name, reset=reset)
        p13.name_set("p13")
        p31.name_set("p31")
        p33.name_set("p33")
        p12 = p11.splitVertical("p12")
        p14 = p13.splitVertical("p14")
        p21 = p11.splitHorizontal("p21")
        p22 = p12.splitHorizontal("p22")
        p23 = p13.splitHorizontal("p23")
        p24 = p14.splitHorizontal("p24")

        p41 = p31.splitHorizontal("p41")
        p32 = p31.splitVertical("p32")
        p42 = p41.splitVertical("p42")

        return window

    def test(self):
        """
        kosmos 'j.servers.tmux.test()'

        :return:
        """
        j.builders.system.package.ensure("htop")

        self.panes_2x2_get()
        window = self.window_get("multi")
        for pane in window.panes:
            pane.execute("clear;echo %s" % pane.name)

        p = self.execute("ls /", "multi", "p22")

        assert p.process_obj.name() == "bash"

        time.sleep(2)
        p.process_obj_child

        assert p.process_obj_child == None

        p = self.execute("htop", "multi", "p22")

        assert p.process_obj.is_running()
        # assert p.process_obj.name()=="htop"

        assert len(p.process_obj_children) == 1

        assert p.process_obj.name() == "bash"

        time.sleep(2)
        p.process_obj_child

        assert p.process_obj_child.name() == "htop"

        assert p.process_obj.name() == "bash"

        assert p.process_obj_child.name() == "htop"

        p = self.execute("find /tmp", "test", "test")

        res = p.out_get()
        p = self.pane_get("test2", "test2", reset=True)

        self._log_info("tests ok for tmux")
