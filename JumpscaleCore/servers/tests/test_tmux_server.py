from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, unittest


class TestTmuxServer(BaseTest):
    def setUp(self):
        self.info("​Install tmux server.")
        j.servers.tmux.install()

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/93")
    def test01_tmux_create_new_session(self):
        """
        - ​Install tmux server.
        - Create new session.
        - Check that created session exist session list.
        - Check that tmux session opened with right name.
        """
        self.info("Create new session.")
        session_name = self.rand_string()
        j.servers.tmux.server.new_session(session_name)

        self.info("Check that created session exist session list.")
        sessions_list = j.servers.tmux.server.list_sessions()
        self.assertIn(session_name, sessions_list)

        self.info("Check that tmux session opened with right name.")
        output, error = self.os_command("tmux ls")
        self.assertIn(session_name, output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/93")
    def test02_tmux_kill_session(self):
        """
        - ​Install tmux server.
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
        self.assertIn("no server running", output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/93")
    def test03_tmux_kill_server(self):
        """
        - ​Install tmux server.
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
        self.assertFalse(sessions_list)
        output, error = self.os_command("tmux ls")
        self.assertIn("no server running", output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/93")
    def test04_tmux_excute(self):
        """
        - Create new session.
        - Run server or process in created tmux session using execute.
        - Check that tmux session deleted successfully.
        """
        self.info("Create new session.")
        session_name = self.rand_string()
        j.servers.tmux.server.new_session(session_name)
        sessions_list = j.servers.tmux.server.list_sessions()

        self.info("Run server or process in created tmux session using execute.")
        j.servers.tmux.execute("python -m SimpleHTTPServer", window=session_name)

        self.info("Check that tmux session deleted successfully.")
        output, error = self.os_command("ps -aux | grep -v grep | grep '{}'".format("python -m SimpleHTTPServer"))
        self.assertFalse(output.decode())
        self.assertEqual(sessions_list, j.servers.tmux.server.list_sessions())
        j.servers.tmux.server.kill_server()
