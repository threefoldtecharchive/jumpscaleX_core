from Jumpscale import j
import random, requests, uuid, time, subprocess
from parameterized import parameterized
from loguru import logger

LOGGER = logger
LOGGER.add("startupcmd_tests_{time}.log")

skip = j.baseclasses.testtools._skip


def info(message):
    LOGGER.info(message)


def os_command(command):
    info("Execute : {} ".format(command))
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    return output, error


def rand_string(size=10):
    return str(uuid.uuid4()).replace("-", "")[1:10]


@parameterized.expand(["background", "tmux", "foreground"])
@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/101")
def test_01_startupcmd_executor(executor):
    """
    - ​Get startupcmd server instance.
    - Define executer type.
    - Add process cmd_start.
    - Start startupcmd server.
    - Check that process running successfully in right executor.
    - Check that server connection  works successfully
    """
    info("Get startupcmd server instance.")
    instance_name = rand_string(6)
    startupcmd_server = j.servers.startupcmd.get(instance_name)

    info("Define executer type.")
    startupcmd_server.executor = executor

    info("Add process cmd_start.")
    startupcmd_server.cmd_start = "python -m SimpleHTTPServer"
    info("Start startupcmd server")
    if executor == "foreground":
        tmux_session_name = rand_string()
        output, error = os_command(
            'tmux new -d -s {} \'kosmos -p "j.servers.startupcmd.get(\\"{}\\").start()"\''.format(
                tmux_session_name, startupcmd_server.name
            )
        )
    else:
        startupcmd_server.start()

    info("Check that process running successfully in right executor.")
    time.sleep(5)
    output, error = os_command(
        " ps -aux | grep -v grep | grep \"startupcmd_{} -m {}\" | awk '{{print $2}}'".format(
            startupcmd_server.name, "SimpleHTTPServer"
        )
    )
    assert output.decode() is not None
    server_PID = output.decode()
    if executor == "tmux":
        output, error = os_command("tmux list-windows")
        assert startupcmd_server.name in output.decode()

    info("Check that server connection  works successfully.")
    output, error = os_command("netstat -nltp | grep '{}' ".format(server_PID))
    assert output.decode() is not None

    info(" Stop server , check it stoped successfully.")
    startupcmd_server.stop()
    time.sleep(5)
    if executor == "tmux":
        output, error = os_command("tmux list-windows")
        assert startupcmd_server.name not in output.decode()
    output, error = os_command(
        " ps -aux | grep -v grep | grep \"startupcmd_{} -m {}\" | awk '{{print $2}}'".format(
            startupcmd_server.name, "SimpleHTTPServer"
        )
    )
    assert output.decode() == ""
    startupcmd_server.delete()


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/101")
def test_02_startupcmd_executor_corex():
    """
    - ​Get startupcmd server instance.
    - Define executer type as corex.
    - Install, start corex server and get its client.
    - Pass process cleint to startcmd server.
    - Start startupcmd , check it works successfully in corex executor . 
    - Check that server connection  works successfully
    """
    info("Get startupcmd server instance.")
    startupcmd_server = j.servers.startupcmd.get()

    info("Define executer type as corex.")
    startupcmd_server.executor = "corex"

    info("Install, start corex server and get its client.")
    j.servers.corex.install()
    j.servers.corex.default.start()
    corex = j.servers.corex.default.client

    info("Pass process cleint to startcmd server.")
    startupcmd_server.executor = "corex"
    startupcmd_server.corex_client_name = corex.name
    startupcmd_server.cmd_start = "python3 -m http.server"

    info("Start startupcmd , check it works successfully in corex executor ")
    startupcmd_server.start()
    output, error = os_command(" ps -aux | grep -v grep | grep {} | awk '{{print $2}}'".format("http.server"))
    assert output.decode() is not None

    info(" * Check that server connection  works successfully.")
    server_PID = output.decode()
    output, error = os_command("netstat -nltp | grep '{}' ".format(server_PID))
    assert output.decode() is not None


@parameterized.expand(["JUMPSCALE", "PYTHON", "BASH"])
@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/101")
def test_03_startupcmd_interpreter(interpreter):
    """
    - ​Get startupcmd server instance.
    - Define interpreter type.
    - Add command in cmd_start .
    - Start startupcmd , check it works successfully . 
    """
    info("​Get startupcmd server instance")
    startupcmd_server = j.servers.startupcmd.get()
    info("Define interpreter type.")
    startupcmd_server.interpreter = interpreter

    info("Add {} command in cmd_start.".format(interpreter))
    file_name = rand_string()
    if interpreter == "JUMPSCALE":
        startupcmd_server.cmd_start = "j.sal.fs.createEmptyFile('/root/{}')".format(file_name)
    elif interpreter == "PYTHON":
        startupcmd_server.cmd_start = "open('/root/{}','w+')".format(file_name)

    elif interpreter == "BASH":
        startupcmd_server.cmd_start = "touch /root/{}".format(file_name)

    info("Start startupcmd , check it works successfully .")
    startupcmd_server.start()
    output, error = os_command("ls /root")
    assert file_name in output.decode()

    startupcmd_server.stop()
    startupcmd_server.delete()


def test_04_startupcmd_jumpscale_gevent_interpreter():
    """
    - ​Get startupcmd server instance.
    - Define interpreter type as JUMPSCALE_GEVENT.
    - Use rack server as cmd start.
    - Start startupcmd ,should start rack server successfully.
    - Stop startupcmd, should stop rack server successfully.
    """
    info("Get startupcmd server instance.")
    instance_name = rand_string(6)
    startupcmd_server = j.servers.startupcmd.get(instance_name)

    info("Define interpreter type.")
    startupcmd_server.interpreter = "JUMPSCALE_GEVENT"

    info("Use rack server as cmd start.")
    port = random.randint(100, 999)
    cmd_start = "j.servers.rack.get().bottle_server_add(port={})&j.servers.rack.get().start()".format(port)
    startupcmd_server.cmd_start = cmd_start
    startupcmd_server.executor = "TMUX"

    info("Start startupcmd ,should start rack server successfully.")
    startupcmd_server.start()
    time.sleep(10)
    output, error = os_command("netstat -nltp | grep {}".format(port))
    import ipdb

    ipdb.set_trace()
    assert output.decode() is not None

    info("Stop startupcmd, should stop rack server successfully.")
    startupcmd_server.stop()
    time.sleep(10)
    output, error = os_command("netstat -nltp | grep {}".format(port))
    assert output.decode() == ""
    startupcmd_server.delete()
