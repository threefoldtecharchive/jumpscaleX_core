from Jumpscale import j
from loguru import logger
import subprocess, time, uuid


def info(message):
    logger.info(message)


def rand_string(self, size=10):
    return str(uuid.uuid4()).replace("-", "")[1:10]


def os_command(command):
    info("Execute : {} ".format(command))
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    return output, error


def test01_tmux_create_new_session():
    """
    - Create new session.
    - Check that created session exist session list.
    - Check that tmux session opened with right name.
    """
    info("Create new session.")
    session_name = rand_string()
    j.servers.tmux.server.new_session(session_name)

    info("Check that created session exist session list.")
    sessions_list = j.servers.tmux.server.list_sessions()
    assert [session for session in sessions_list if session.name == session_name]

    info("Check that tmux session opened with right name.")
    output, error = os_command("tmux ls")
    assert session_name in output.decode()
    j.servers.tmux.server.kill_server()


def test02_tmux_kill_session():
    """
    - Create new session.
    - Kill created session.
    - Check that tmux session deleted successfully.
    """
    info("Create new session.")
    session_name = rand_string()
    j.servers.tmux.server.new_session(session_name)

    info("Kill created session.")
    j.servers.tmux.server.kill_session(session_name)

    info("check that tmux session deleted successfully.")
    sessions_list = j.servers.tmux.server.list_sessions()
    assert session_name not in sessions_list
    output, error = os_command("tmux ls")
    assert session_name not in output.decode()


def test03_tmux_kill_server():
    """
    - Create two sessions.
    - Kill server.
    - Check that tmux server  and two sessions killed successfully.
    """
    info("Create two sessions.")
    session_name1 = rand_string()
    session_name2 = rand_string()
    j.servers.tmux.server.new_session(session_name1)
    j.servers.tmux.server.new_session(session_name2)

    info("Kill server.")
    j.servers.tmux.server.kill_server()

    info("check  that tmux server  and two sessions killed successfully .")
    sessions_list = j.servers.tmux.server.list_sessions()
    assert [session for session in sessions_list if session.name == session_name1] is False
    assert [session for session in sessions_list if session.name == session_name2] is False

    output, error = os_command("tmux ls")
    assert session_name1 not in output.decode()
    assert session_name1 not in output.decode()


def test04_tmux_excute():
    """
    - Create new session.
    - Run server or process in created tmux session using execute.
    - Kill created session.
    - Check that server has been killed successfully.
    """
    window_name = rand_string()

    info("Run server or process in created tmux session using execute.")
    j.servers.tmux.execute("python -m SimpleHTTPServer", window=window_name)
    time.sleep(5)
    output, error = os_command("ps -aux | grep -v grep | grep '{}'".format("python -m SimpleHTTPServer"))
    assert output.decode()

    info("Kill created session.")
    j.servers.tmux.window_kill(window_name)

    info("Check that server has been killed successfully.")
    output, error = os_command("ps -aux | grep -v grep | grep '{}'".format("python -m SimpleHTTPServer"))
    assert output.decode() is False
