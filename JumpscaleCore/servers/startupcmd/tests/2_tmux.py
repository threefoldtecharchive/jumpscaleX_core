from Jumpscale import j

startupcmd = j.servers.startupcmd


def test_tmux():
    """
    to run:

    kosmos 'j.servers.startupcmd.test(name="tmux")' --debug
    """

    startupcmd.http.cmd_start = "python3 -m http.server"  # starts on port 8000
    startupcmd.http.ports = 8000
    startupcmd.http.start()
    assert startupcmd.http.pid
    startupcmd.http.timeout = 5
    assert startupcmd.http.is_running()
    startupcmd.http.stop()
    assert not startupcmd.http.is_running()

    return "OK"
