import os
from Jumpscale import j
import random, unittest, time
from parameterized import parameterized
from uuid import uuid4
from loguru import logger
import subprocess

skip = j.baseclasses.testtools._skip
LOGGER = logger
LOGGER.add("SAL_PROCESS_{time}.log")


def info(message):
    LOGGER.info(message)


def rand_string(size=10):
    return str(uuid4())[:size]


def os_command(command):
    info("Execute : {} ".format(command))
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    return output, error


def after():
    output, error = os_command("ps -aux | grep -v -e grep -e tmux | grep 'tail -f' | awk '{{print $2}}'")
    if output:
        pids = output.decode().splitlines()
        os_command(f"kill -9 {' '.join(pids)}")

    output, error = os_command("ps -aux | grep -v -e grep -e tmux | grep 'SimpleHTTPServer' | awk '{{print $2}}'")
    if output:
        pids = output.decode().splitlines()
        os_command(f"kill -9 {' '.join(pids)}")


def test01_checkInstalled():
    """TC401
    Test case to check specific command installed or not.

    **Test scenario**
    #. Use CheckInstalled method to check that curl installed.
    #. Use CheckInstalled method to check that nodejs uninstalled.
    """
    info("Use CheckInstalled method to check that curl installed.")
    assert j.sal.process.checkInstalled("curl") is True

    info("Use CheckInstalled method to check that nodejs uninstalled .")
    assert j.sal.process.checkInstalled("nodejs") is False


def test02_checkProcessForPid():
    """TC402
    Test case to test checkProcessForPid method.

    **Test scenario**
    #. Start process [p1], get its pid[PID1].
    #. Use checkProcessForPid method with process [P1] and PID1, should return 0.
    #. Start another process [P2], and get its pid [PID2].
    #. Use checkProcessForPid method with process[P1] and pid[PID2], should return 1.
    #. Use checkProcessForPid method with process[P2] and pid[PID1], should return 1.
    #. Kill process[P1] and [P2], use checkProcessForPid with[P1] and PID1, should return 1.
    """
    info("Start process [p1], get its pid[PID1].")
    PT = random.randint(1000, 2000)
    output, error = os_command("tmux  new -d -s {} 'python -m SimpleHTTPServer {}' ".format(rand_string(), PT))
    time.sleep(2)
    output, error = os_command(" ps -aux | grep -v -e tmux -e  grep  | grep SimpleHTTPServer | awk  '{{print $2}}'")
    assert output.decode("utf-8") != ""
    PID_1 = int(output.decode())

    info("Use checkProcessForPid method with process [P1] and PID1, should return 0.")
    assert j.sal.process.checkProcessForPid(PID_1, "python") == 0

    info("Start another process [p2], get its pid[PID2].")
    output, error = os_command("tmux  new -d -s {} 'tail -f /dev/null'".format(rand_string()))
    time.sleep(2)
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux | grep '{}' | awk '{{print $2}}'".format("tail -f"))
    assert output.decode("utf-8") != ""
    PID_2 = int(output.decode())

    info("Use checkProcessForPid method with process[P1] and wrong pid[PID2], should return 1.")
    assert j.sal.process.checkProcessForPid(PID_2, "python") == 1

    info("Use checkProcessForPid method with process[P2] and pid[PID1], should return 1.")
    assert j.sal.process.checkProcessForPid(PID_1, "tail") == 1

    info("Kill process[P1] and [P2], use checkProcessForPid with[P1] and PID1, should return 1.")
    output, error = os_command("kill -9 {} {}".format(PID_1, PID_2))
    time.sleep(2)
    assert j.sal.process.checkProcessForPid(PID_1, "python") == 1


def test03_checkProcessRunning():
    """TC403
    Test case to test checkProcessRunning method.

    **Test scenario**
    #. Start process [p1].
    #. Use checkProcessRunning method with process [P1], should True.
    #. Stop process [P1].
    #. Use checkProcessRunning method with process [P1], should False.
    """
    info("Start process [p1].")
    PT = random.randint(1000, 2000)
    output, error = os_command("tmux  new -d -s {} 'python -m SimpleHTTPServer {}'".format(rand_string(), PT))
    time.sleep(2)

    info("Use checkProcessRunning method with process [P1], should True.")
    assert j.sal.process.checkProcessRunning("SimpleHTTPServer") is True

    info("Stop process [p1].")
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux  | grep SimpleHTTPServer | awk '{{print $2}}'")
    assert output.decode("utf-8") != ""
    PID = int(output.decode())
    output, error = os_command("kill -9 {}".format(PID))
    time.sleep(2)

    info("Use checkProcessRunning method with process [P1], should return False.")
    assert j.sal.process.checkProcessRunning("SimpleHTTPServer") is False


def test04_execute_process():
    """TC404
    Test case to test process method.

    **Test scenario**
    #. Use execute command to start process, should work successfully.
    """
    info("Use execute command to start process, should work successfully.")
    PT = random.randint(1000, 2000)
    process = "tmux  new -d -s {} 'python -m SimpleHTTPServer {}'".format(rand_string(), PT)
    j.sal.process.execute(process)
    time.sleep(2)
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux | grep SimpleHTTPServer | awk '{{print $2}}'")
    assert output.decode("utf-8") != ""
    PID = int(output.decode())
    output, error = os_command("kill -9 {}".format(PID))


@parameterized.expand(["process", "pids"])
def test05_getByPort(result_type):
    """TC405
    Test case to test get process or pids by port methods.

    **Test scenario**
    #. Start process [P] in specific port [PT].
    #. Get process[P] PID.
    #. Use getProcessByPort to get P or getPidsByPort to get PID, should succeed.
    """
    info("Start process [P] in specific port [PT]")
    PT = random.randint(10, 800)
    P = "SimpleHTTPServer"
    output, error = os_command("tmux  new -d -s {} 'python -m {} {}' ".format(rand_string(), P, PT))
    time.sleep(2)

    info("Get process [P] Pid.")
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux | grep {} | awk '{{print $2}}'".format(P))
    assert output.decode("utf-8") != ""
    PID = int(output.decode())
    if result_type == "process":
        info("Use getProcessByPort to get P, should succeed.")
        process = j.sal.process.getProcessByPort(PT)
        assert process.name() == "python"
    elif result_type == "pids":
        info("Use getPidsByPort to get PID, should succeed.")
        process_pid = j.sal.process.getPidsByPort(PT)
        assert PID == process_pid[0]
    output, error = os_command("kill -9 {} ".format(PID))


def test06_getDefunctProcesses():
    """TC406
    Test case to test get process methods.

    **Test scenario**
    #. Get zombie processes list [z1] by ps -aux.
    #. Get zombie processes list [z2] by getDefunctProcesses.
    #. [z1] and [z2] should be same.
    """
    info("Get zombie processes list [z1] by ps -aux")
    output, error = os_command("ps aux | awk '{{ print $8 " " $2 }}' | grep -w Z ")
    z1 = output.decode().splitlines()
    z1 = list(map(int, z1))
    info("Get zombie processes list [z2] by getDefunctProcesses ")
    z2 = j.sal.process.getDefunctProcesses()

    info("[z1] and [z2] should be same.")
    assert z1 == z2


def test07_getPidsByFilter():
    """TC407
    Test case to test get processes pids by specific filter. 

    **Test scenario**
    #. Get all processes PIDs which using python[PIDs_1].
    #. Use getPidsByFilter method to get processess PIDs which using python[PIDs_2].
    #. Compare PIDs_1 and PIDs_2 should be same.
    """
    info("Get all processes PIDs which using  python[PIDs_1].")
    output, error = os_command(" ps -aux | grep -v grep | grep python | awk '{{print $2}}'")
    PIDS_1 = output.decode().splitlines()
    PIDS_1 = list(map(int, PIDS_1))

    info("Use getPidsByFilter method  to get processess PIDs which using python[PIDs_2].")
    PIDS_2 = j.sal.process.getPidsByFilter("python")

    info(" Compare PIDs_1 and PIDs_2 should be same.")
    assert len(PIDS_1) == len(PIDS_2)
    assert sorted(PIDS_1) == sorted(PIDS_2)


def test08_getProcessObject():
    """ TC408
    Test case to test getProcessObject. 

    **Test scenario**
    #. Start process [P] with python.
    #. Use getProcessObject to get object of process.
    #. Check it works correctly.
    #. Kill the process [P] using process object, check it works sucessfuly.
    #  Try to get object of this process again, should fail.
    """
    info("Start process [p1] with python.")
    PT = random.randint(1000, 2000)
    output, error = os_command("tmux  new -d -s {} 'python -m SimpleHTTPServer {}' ".format(rand_string(), PT))
    time.sleep(2)
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux | grep SimpleHTTPServer | awk '{{print $2}}'")
    assert output.decode("utf-8") != ""
    PID = int(output.decode())

    info("Use getProcessObject to get object of process.")
    process_object = j.sal.process.getProcessObject(PID)

    info("Check it works correctly.")
    assert process_object.name() == "python"
    assert process_object.pid == PID

    info("Kill the process [P] using process object, check it works sucessfuly.")
    process_object.kill()
    time.sleep(2)
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux | grep SimpleHTTPServer | awk '{{print $2}}'")
    assert output.decode("utf-8") == ""

    info("Try to get object of this process again, should fail.")
    try:
        output = j.sal.process.getProcessObject(PID)
        raise "error should be raised"
    except Exception as e:
        info("Error should be raised not exist process")


def test09_getProcessPid_and_getProcessPidsFromUser():
    """ TC 409
    Test case to test getProcessPid. 

    **Test scenario**
    #. Start process [P] with python get its user and pid.
    #. Use getProcessPid to get process pid [PID], Check that it returns right PID.
    #. Use getProcessPidsFromUser to get process pid [PID], Check that it returs right PID.
    """
    info("Start process [p1] with python.")
    P = "python -m SimpleHTTPServer {}".format(random.randint(1000, 2000))
    output, error = os_command("tmux  new -d -s {} '{}'  ".format(rand_string(), P))
    time.sleep(2)
    output, error = os_command("ps ax | grep -v grep | grep SimpleHTTPServer | awk '{print $1}'")
    pids = output.decode().split()
    pids = list(map(int, pids))
    assert len(pids) == 2

    output, error = os_command("ps -aux | grep -v grep | grep SimpleHTTPServer | awk '{print $1}'| tail -n+2")
    user = output.decode().strip()

    info("Use getProcessPid to get process pid [PID], Check that it returns right PID.")
    assert pids == j.sal.process.getProcessPid(P)

    info("Use getProcessPidsFromUser to get process pid [PID], Check that it returs right PID.")
    assert set(pids).issubset(set(j.sal.process.getProcessPidsFromUser(user))) is True

    output, error = os_command("kill -9 {} {}".format(pids[0], pids[1]))


def test10_isPidAlive():
    """TC410
    Test case to test isPidAlive. 

    **Test scenario**
    #. Start process [P] with python get its user and pid.
    #. Use isPidAlive, should return True.
    #. Kill process [P].
    #. Use isPidAlive, should return False.
    """
    info("Stat process [p1] with python.")
    P = "python -m SimpleHTTPServer"
    output, error = os_command("tmux  new -d -s {} '{}'  ".format(rand_string(), P))
    time.sleep(2)
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux | grep SimpleHTTPServer | awk '{{print $2}}'")
    assert output.decode("utf-8") != ""
    PID = int(output.decode())

    info("Use isPidAlive, should return True.")
    assert j.sal.process.isPidAlive(PID) is True

    info("Kill process [P].")
    output, error = os_command("kill -9 {}".format(PID))

    info("Use isPidAlive, should return False.")
    time.sleep(10)
    assert j.sal.process.isPidAlive(PID) is False


@parameterized.expand(["kill", "killProcessByName", "killUserProcesses", "killall"])
def test11_kill_process(filter):
    """TC411
    Test case to test all kill process methods.

    **Test scenario**
    #. Start process [P1], gets its PID1.
    #. Create new user.
    #. Start process [P2] with new user, gets its PID2.
    #. Kill the process using one of kill methods ["kill", "killProcessByName", "killUserProcesses", "killall"].
    #. Check that process killed successfully.
    """
    info("Start process [p1].")
    P1 = "tail -f /dev/null"
    output, error = os_command("tmux  new -d -s {} '{}'  ".format(rand_string(), P1))
    time.sleep(2)
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux | grep '{}' | awk '{{print $2}}'".format(P1))
    assert output.decode("utf-8") != ""
    PID_1 = int(output.decode())

    info("Create new user.")
    new_user = rand_string()
    output, error = os_command("sudo useradd {}".format(new_user))

    info("Start process [P2] with new user, gets its PID2.")
    new_file = rand_string()
    output, error = os_command("touch /home/{}".format(new_file))
    P2 = "tail -f /home/{}".format(new_file)
    output, error = os_command("tmux  new -d -s {} 'sudo -u {} {}'  ".format(rand_string(), new_user, P2))
    time.sleep(2)
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux -e sudo | grep '{}' | awk '{{print $2}}'".format(P2))
    assert output.decode("utf-8") != ""
    PID_2 = int(output.decode())

    info("kill the process using {}".format(filter))
    if filter == "kill":
        j.sal.process.kill(PID_2)

    elif filter == "killProcessByName":
        j.sal.process.killProcessByName("/home/{}".format(new_file))

    elif filter == "killUserProcesses":
        j.sal.process.killUserProcesses(new_user)
    else:
        j.sal.process.killall("tail")
    time.sleep(2)

    info("Check that processes killed successfully.")
    output, error = os_command(" ps -aux | grep -v -e grep -e tmux | grep tail | awk '{{print $2}}'")
    result = output.decode().splitlines()
    result = list(map(int, result))

    if filter == "killall":
        assert output.decode("utf-8") == ""
    else:
        assert PID_1 in result
        assert PID_2 not in result
        output, error = os_command("kill -9 {} ".format(PID_1))
