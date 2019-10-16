from .base_test import BaseTest
from Jumpscale import j
import random, unittest, time
from parameterized import parameterized


class PROCESS(BaseTest):
    def setUp(self):
        pass

    def test01_checkInstalled(self):
        """TC401
        Test case to check specific command installed or not.

        **Test scenario**
        #. Use CheckInstalled method to check that curl installed.
        #. Use CheckInstalled method to check that nodejs uninstalled.
        """
        self.info("Use CheckInstalled method to check that curl installed.")
        self.assertTrue(j.sal.process.checkInstalled("curl"))

        self.info("Use CheckInstalled method to check that nodejs uninstalled .")
        self.assertFalse(j.sal.process.checkInstalled("nodejs"))

    def test02_checkProcessForPid(self):
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
        self.info("Start process [p1], get its pid[PID1].")
        PT = random.randint(1000, 2000)
        output, error = self.os_command(
            "tmux  new -d -s {} 'python -m SimpleHTTPServer {}' ".format(self.rand_string(), PT)
        )
        output, error = self.os_command(
            " ps -aux | grep -v -e tmux -e  grep  | grep SimpleHTTPServer | awk  '{{print $2}}'"
        )
        PID_1 = int(output.decode())

        self.info("Use checkProcessForPid method with process [P1] and PID1, should return 0.")
        self.assertEqual(j.sal.process.checkProcessForPid(PID_1, "python"), 0)

        self.info("Start another process [p2], get its pid[PID2].")
        output, error = self.os_command("tmux  new -d -s {} 'tail -f /dev/null'".format(self.rand_string()))
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux | grep '{}' | awk '{{print $2}}'".format("tail -f")
        )
        PID_2 = int(output.decode())

        self.info("Use checkProcessForPid method with process[P1] and wrong pid[PID2], should return 1.")
        self.assertEqual(j.sal.process.checkProcessForPid(PID_2, "python"), 1)

        self.info("Use checkProcessForPid method with process[P2] and pid[PID1], should return 1.")
        self.assertEqual(j.sal.process.checkProcessForPid(PID_1, "tail"), 1)

        self.info("Kill process[P1] and [P2], use checkProcessForPid with[P1] and PID1, should return 1.")
        output, error = self.os_command("kill -9 {} {}".format(PID_1, PID_2))
        self.assertEqual(j.sal.process.checkProcessForPid(PID_1, "python"), 1)

    def test03_checkProcessRunning(self):
        """TC403
        Test case to test checkProcessRunning method.

        **Test scenario**
        #. Start process [p1].
        #. Use checkProcessRunning method with process [P1], should True.
        #. Stop process [P1].
        #. Use checkProcessRunning method with process [P1], should False.
        """
        self.info("Start process [p1].")
        PT = random.randint(1000, 2000)
        output, error = self.os_command(
            "tmux  new -d -s {} 'python -m SimpleHTTPServer {}'".format(self.rand_string(), PT)
        )

        self.info("Use checkProcessRunning method with process [P1], should True.")
        self.assertTrue(j.sal.process.checkProcessRunning("SimpleHTTPServer"))

        self.info("Stop process [p1].")
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux  | grep SimpleHTTPServer | awk '{{print $2}}'"
        )
        PID = int(output.decode())
        output, error = self.os_command("kill -9 {}".format(PID))

        self.info("Use checkProcessRunning method with process [P1], should return False.")
        self.assertFalse(j.sal.process.checkProcessRunning("SimpleHTTPServer"))

    def test04_execute_process(self):
        """TC404
        Test case to test process method.

        **Test scenario**
        #. Use execute command to start process, should work successfully.
        """
        self.info("Use execute command to start process, should work successfully.")
        PT = random.randint(1000, 2000)
        process = "tmux  new -d -s {} 'python -m SimpleHTTPServer {}'".format(self.rand_string(), PT)
        j.sal.process.execute(process)
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux | grep SimpleHTTPServer | awk '{{print $2}}'"
        )
        self.assertTrue(output)
        PID = int(output.decode())
        output, error = self.os_command("kill -9 {}".format(PID))

    @parameterized.expand(["process", "pids"])
    def test05_getByPort(self, result_type):
        """TC405
        Test case to test get process or pids by port methods.

        **Test scenario**
        #. Start process [P] in specific port [PT].
        #. Get process[P] PID.
        #. Use getProcessByPort to get P or getPidsByPort to get PID, should succeed.
        """
        if result_type == "pids":
            self.skipTest("https://github.com/threefoldtech/jumpscaleX_core/issues/122")

        self.info("Start process [P] in specific port [PT]")
        PT = random.randint(10, 800)
        P = "SimpleHTTPServer"
        output, error = self.os_command("tmux  new -d -s {} 'python -m {} {}' ".format(self.rand_string(), P, PT))

        self.info("Get process [P] Pid.")
        output, error = self.os_command(" ps -aux | grep -v -e grep -e tmux | grep {} | awk '{{print $2}}'".format(P))
        PID = int(output.decode())
        time.sleep(10)
        if result_type == "process":
            self.info("Use getProcessByPort to get P, should succeed.")
            process = j.sal.process.getProcessByPort(PT)
            self.assertEqual(process.name(), "python")
        elif result_type == "pids":
            self.info("Use getPidsByPort to get PID, should succeed.")
            process_pid = j.sal.process.getPidsByPort(PT)
            self.assertEqual(PID, process_pid)
        output, error = self.os_command("kill -9 {} ".format(PID))

    def test06_getDefunctProcesses(self):
        """TC406
        Test case to test get process methods.

        **Test scenario**
        #. Get zombie processes list [z1] by ps -aux.
        #. Get zombie processes list [z2] by getDefunctProcesses.
        #. [z1] and [z2] should be same.
        """
        self.info("Get zombie processes list [z1] by ps -aux")
        output, error = self.os_command("ps aux | awk '{{ print $8 " " $2 }}' | grep -w Z ")
        z1 = output.decode().splitlines()
        z1 = list(map(int, z1))
        self.info("Get zombie processes list [z2] by getDefunctProcesses ")
        z2 = j.sal.process.getDefunctProcesses()

        self.info("[z1] and [z2] should be same.")
        self.assertEqual(z1, z2)

    def test07_getPidsByFilter(self):
        """TC407
        Test case to test get processes pids by specific filter. 

        **Test scenario**
        #. Get all processes PIDs which using python[PIDs_1].
        #. Use getPidsByFilter method to get processess PIDs which using python[PIDs_2].
        #. Compare PIDs_1 and PIDs_2 should be same.
        """
        self.info("Get all processes PIDs which using  python[PIDs_1].")
        output, error = self.os_command(" ps -aux | grep -v grep | grep python | awk '{{print $2}}'")
        PIDS_1 = output.decode().splitlines()
        PIDS_1 = list(map(int, PIDS_1))
        self.info("Use getPidsByFilter method  to get processess PIDs which using python[PIDs_2].")
        PIDS_2 = j.sal.process.getPidsByFilter("python")

        self.info(" Compare PIDs_1 and PIDs_2 should be same.")
        self.assertEqual(len(PIDS_1), len(PIDS_2))
        self.assertEqual(sorted(PIDS_1), sorted(PIDS_2))

    def test08_getProcessObject(self):
        """ TC408
        Test case to test getProcessObject. 

        **Test scenario**
        #. Start process [P] with python.
        #. Use getProcessObject to get object of process.
        #. Check it works correctly.
        #. Kill the process [P] using process object, check it works sucessfuly.
        #  Try to get object of this process again, should fail.
        """
        self.info("Start process [p1] with python.")
        PT = random.randint(1000, 2000)
        output, error = self.os_command(
            "tmux  new -d -s {} 'python -m SimpleHTTPServer {}' ".format(self.rand_string(), PT)
        )
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux | grep SimpleHTTPServer | awk '{{print $2}}'"
        )
        PID = int(output.decode())

        self.info("Use getProcessObject to get object of process.")
        process_object = j.sal.process.getProcessObject(PID)

        self.info("Check it works correctly.")
        self.assertEqual(process_object.name(), "python")
        self.assertEqual(process_object.pid, PID)

        self.info("Kill the process [P] using process object, check it works sucessfuly.")
        process_object.kill()
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux | grep SimpleHTTPServer | awk '{{print $2}}'"
        )
        self.assertFalse(output.decode())
        time.sleep(10)

        self.info("Try to get object of this process again, should fail.")
        with self.assertRaises(Exception):
            process_object = j.sal.process.getProcessObject(PID)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/122")
    def test09_getProcessPid_and_getProcessPidsFromUser(self):
        """ TC 409
        Test case to test getProcessPid. 

        **Test scenario**
        #. Start process [P] with python get its user and pid.
        #. Use getProcessPid to get process pid [PID], Check that it returs right PID.
        #. Use getProcessPidsFromUser to get process pid [PID], Check that it returs right PID.
        """
        self.info("Start process [p1] with python.")
        P = "python -m SimpleHTTPServer {}".format(random.randint(1000, 2000))
        output, error = self.os_command("tmux  new -d -s {} '{}'  ".format(self.rand_string(), P))
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux | grep SimpleHTTPServer | awk '{print $1 \" \" $2 }'"
        )
        result = output.decode().split()
        self.assertEqual(len(result), 2)
        user = result[0]
        PID = result[1]

        self.info("Use getProcessPid to get process pid [PID], Check that it returs right PID.")
        self.assertEqual(PID, j.sal.process.getProcessPid(P))

        self.info("Use getProcessPidsFromUser to get process pid [PID], Check that it returs right PID.")
        self.assertIn(PID, j.sal.process.getProcessPidsFromUser(user))

        output, error = self.os_command("kill -9 {} ".format(PID))

    def test10_isPidAlive(self):
        """TC410
        Test case to test isPidAlive. 

        **Test scenario**
        #. Start process [P] with python get its user and pid.
        #. Use isPidAlive, should return True.
        #. Kill process [P].
        #. Use isPidAlive, should return False.
        """
        self.info("Stat process [p1] with python.")
        P = "python -m SimpleHTTPServer"
        output, error = self.os_command("tmux  new -d -s {} '{}'  ".format(self.rand_string(), P))
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux | grep SimpleHTTPServer | awk '{{print $2}}'"
        )
        PID = int(output.decode())

        self.info("Use isPidAlive, should return True.")
        self.assertTrue(j.sal.process.isPidAlive(PID))

        self.info("Kill process [P].")
        output, error = self.os_command("kill -9 {}".format(PID))

        self.info("Use isPidAlive, should return False.")
        time.sleep(10)
        self.assertFalse(j.sal.process.isPidAlive(PID))

    @parameterized.expand(["kill", "killProcessByName", "killUserProcesses", "killall"])
    def test11_kill_process(self, filter):
        """TC411
        Test case to test all kill process methods.

        **Test scenario**
        #. Start process [P1], gets its PID1.
        #. Create new user.
        #. Start process [P2] with new user, gets its PID2.
        #. Kill the process using one of kill methods ["kill", "killProcessByName", "killUserProcesses", "killall"].
        #. Check that process killed successfully.
        """
        if filter in ["killProcessByName", "killUserProcesses"]:
            self.skipTest("https://github.com/threefoldtech/jumpscaleX_core/issues/123")

        self.info("Start process [p1].")
        P1 = "tail -f /dev/null"
        output, error = self.os_command("tmux  new -d -s {} '{}'  ".format(self.rand_string(), P1))
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux | grep '{}' | awk '{{print $2}}'".format(P1)
        )
        PID_1 = int(output.decode())

        self.info("Create new user.")
        new_user = self.rand_string()
        output, error = self.os_command("sudo useradd {}".format(new_user))

        self.info("Start process [P2] with new user, gets its PID2.")
        new_file = self.rand_string()
        output, error = self.os_command("touch /home/{}".format(new_file))
        P2 = "tail -f /home/{}".format(new_file)
        output, error = self.os_command("tmux  new -d -s {} 'sudo -u {} {}'  ".format(self.rand_string(), new_user, P2))
        output, error = self.os_command(
            " ps -aux | grep -v -e grep -e tmux -e sudo | grep '{}' | awk '{{print $2}}'".format(P2)
        )
        PID_2 = int(output.decode())

        self.info("kill the process using {}".format(filter))
        if filter == "kill":
            j.sal.process.kill(PID_2)

        elif filter == "killProcessByName":
            j.sal.process.killProcessByName("/home/{}".format(new_file))

        elif filter == "killUserProcesses":
            j.sal.process.killUserProcesses(new_user)
        else:
            j.sal.process.killall("tail")

        self.info("Check that processes killed successfully.")
        output, error = self.os_command(" ps -aux | grep -v -e grep -e tmux | grep tail | awk '{{print $2}}'")
        result = output.decode().splitlines()
        result = list(map(int, result))

        if filter == "killall":
            self.assertFalse(result)
        else:
            self.assertIn(PID_1, result)
            self.assertNotIn(PID_2, result)
            output, error = self.os_command("kill -9 {} ".format(PID_1))
