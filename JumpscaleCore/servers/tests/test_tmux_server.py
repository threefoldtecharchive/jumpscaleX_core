from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest


class TestTmuxServer(BaseTest):
    def setUp(self):
        pass

    def test01_tmux_create_new_session(self):
        """
        - Create new session.
        - Check that created session exist session list.
        - Check that tmux session opened with right name.
        """
        self.info("Create new session.")
        session_name = self.rand_string()
        j.servers.tmux.server.new_session(session_name)

        self.info("Check that created session exist session list.")
        sessions_list = j.servers.tmux.server.list_sessions()
        self.assertTrue([session for session in sessions_list if session.name == session_name])

        self.info("Check that tmux session opened with right name.")
        output, error = self.os_command("tmux ls")
        self.assertIn(session_name, output.decode())
        j.servers.tmux.server.kill_server()

    def test02_tmux_kill_session(self):
        """
        - Create new session.
        - Kill created session.
        - Check that tmux session deleted successfully.
        """
        self.info("Create new session.")
        session_name = self.rand_string()
        j.servers.tmux.server.new_session(session_name)

        self.info("Kill created session.")
        j.servers.tmux.server.kill_session(session_name)

        self.info("check that tmux session deleted successfully.")
        sessions_list = j.servers.tmux.server.list_sessions()
        self.assertNotIn(session_name, sessions_list)
        output, error = self.os_command("tmux ls")
        self.assertNotIn(session_name, output.decode())

    def test03_tmux_kill_server(self):
        """
        - Create two sessions.
        - Kill server.
        - Check that tmux server  and two sessions killed successfully.
        """
        self.info("Create two sessions.")
        session_name1 = self.rand_string()
        session_name2 = self.rand_string()
        j.servers.tmux.server.new_session(session_name1)
        j.servers.tmux.server.new_session(session_name2)

        self.info("Kill server.")
        j.servers.tmux.server.kill_server()

        self.info("check  that tmux server  and two sessions killed successfully .")
        sessions_list = j.servers.tmux.server.list_sessions()
        self.assertFalse([session for session in sessions_list if session.name == session_name1])
        self.assertFalse([session for session in sessions_list if session.name == session_name2])

        output, error = self.os_command("tmux ls")
        self.assertNotIn(session_name1, output.decode())
        self.assertNotIn(session_name1, output.decode())

    def test04_tmux_excute(self):
        """
        - Create new session.
        - Run server or process in created tmux session using execute.
        - Kill created session.
        - Check that server has been killed successfully.
        """
        window_name = self.rand_string()

        self.info("Run server or process in created tmux session using execute.")
        j.servers.tmux.execute("python -m SimpleHTTPServer", window=window_name)
        output, error = self.os_command("ps -aux | grep -v grep | grep '{}'".format("python -m SimpleHTTPServer"))
        self.assertTrue(output.decode())

        self.info("Kill created session.")
        j.servers.tmux.window_kill(window_name)

        self.info("Check that server has been killed successfully.")
        output, error = self.os_command("ps -aux | grep -v grep | grep '{}'".format("python -m SimpleHTTPServer"))
        self.assertFalse(output.decode())
