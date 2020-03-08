from Jumpscale import j
import random
import uuid, subprocess
import unittest
from parameterized import parameterized

MAIN_ACTORS = ["explorer_proxy", "system"]
skip = j.baseclasses.testtools._skip


def info(message):
    j.tools.logger._log_info(message)


def rand_string(size=10):
    return str(uuid.uuid4()).replace("-", "")[1:10]


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/560")
def before_all():
    pass


def after():
    j.servers.tmux.kill()


def check_threebot_main_running_servers():
    info(" *  Make sure that server started successfully by check zdb ,lapis, sonic,and openresty work.  ")
    info("*** zdb server ***")
    _, zdb_output, error = j.sal.process.execute(" ps -aux | grep -v grep | grep startupcmd_zdb")
    assert zdb_output != ""
    info(" * Check that  zdb server connection  works successfully and right port.")
    assert j.sal.nettools.tcpPortConnectionTest("localhost", 9900) is True

    info("*** sonic  server ***")
    _, sonic_output, error = j.sal.process.execute(" ps -aux | grep -v grep | grep startupcmd_sonic ")
    assert sonic_output != ""
    info(" * Check that  sonic server connection  works successfully.")
    assert j.sal.nettools.tcpPortConnectionTest("localhost", 1491) is True

    info("*** gedis server ***")
    assert j.sal.nettools.tcpPortConnectionTest("localhost", 8901) is True

    info("*** lapis server ***")
    _, lapis_output, error = j.sal.process.execute(" ps -aux | grep -v grep | grep lapis ")
    assert lapis_output != ""
    info("*** openresty ***")
    _, openresty_output, error = j.sal.process.execute(" ps -aux | grep -v grep | grep /sandbox/bin/openresty ")
    assert openresty_output != ""


def Test_01_start():
    """
    - Install  threebot server.
    - Get gedis client from it.
    - Check it works correctly.
    """
    info("Get gedis client from it .")

    gedis_client = j.servers.threebot.start(background=True)

    info(" Check that main servers running successfully.  ")
    check_threebot_main_running_servers()

    info("check main actors loaded successfully.")
    for actor in MAIN_ACTORS:
        try:
            getattr(gedis_client.actors, actor)
        except Exception as e:
            assert 1 == 2, "There is an error with data {}".format(e)


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/560")
def Test_02_start_stop_options():
    """
    - Start server.
    - Make sure that server started successfully by check zdb and sonic works.
    - Check that server connection  works successfully.
    - Stop server
    """
    cl = j.servers.threebot.get()
    cl.start(background=True)
    info(" Check that main servers running successfully.  ")
    check_threebot_main_running_servers()

    info(" * Stop server threebot server. ")
    cl.stop()

    info("Check servers stopped successfully.")
    assert j.sal.nettools.tcpPortConnectionTest("localhost", 9900) is False, "zdb still running."
    assert j.sal.nettools.tcpPortConnectionTest("localhost", 1491) is False, "sonic still running."
    assert j.sal.nettools.tcpPortConnectionTest("localhost", 8901) is False, "Gedis still running."
