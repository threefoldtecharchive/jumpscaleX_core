import unittest
from Jumpscale import j
from random import randint
from testconfig import config
from base_test import BaseTest
from parameterized import parameterized


class SshClient(BaseTest):
    addr = config["ssh"]["addr"]
    port = config["ssh"]["port"]
    login = config["ssh"]["login"]
    passwd = config["ssh"]["passwd"]

    @classmethod
    def setUpClass(cls):
        cls.info("create ssh client")
        cls.SSH_CLIENT = j.clients.ssh.get(
            name="SSH_{}".format(randint(1, 1000)),
            addr=cls.addr,
            port=cls.port,
            login=cls.login,
            passwd=cls.passwd
        )

    @classmethod
    def tearDownClass(cls):
        cls.info("delete ssh client")
        cls.SSH_CLIENT.delete()

    def install_nginx(self):
        self.info("install nginx on remote machine")
        self.os_command('sshpass -p {} ssh root@{} -p {} "sudo apt install nginx -y "'
                        .format(self.passwd, self.addr, self.port))

    def check_nginx_install(self):
        self.info("check that nginx is installed correctly")
        self.install_nginx()

        output, error = self.os_command('sshpass -p {} ssh root@{} -p {} "curl localhost"'
                                        .format(self.passwd, self.addr, self.port))

        self.info("check that nginx is installed correctly on remote machine")
        if "Welcome to nginx!" in output.decode():
            return True
        else:
            return False

    def test001_addr_variable_properites(self):
        """
        TC 509
        Test case to test addr variable property

        **Test scenario**
        #. check the output from addr variable property it should equal to addr of remote ssh machine.
        """

        self.info("check addr variable property")
        self.assertEqual(self.SSH_CLIENT.addr_variable, self.addr)

    def test002_port_variable_property(self):
        """
        TC 510
        Test case to test port variable property.

        **Test scenario**
        #. check the output from port variable property it should equal to port of remote ssh machine.
        """

        self.info("check port variable property")
        self.assertEqual(str(self.SSH_CLIENT.port_variable), str(self.port))

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/206")
    def test003_is_connected_property(self):
        """
        TC 511
        Test case to test is_connected property.

        **Test scenario**
        #. check that is_connected property is True.
        """

        self.info("check that is_connected property is True")
        self.assertTrue(self.SSH_CLIENT.isconnected)

    def test004_file_copy_valid_file_local_and_valid_file_remote(self):
        """
        TC 485
        Test case for file_copy method, valid local file and valid remote file, should pass

        **Test scenario**
        #. create test file, in local machine.
        #. copy this file to remote machine.
        #. make sure that the file is copied correctly
        """

        self.info("create file locally")
        with open('/tmp/ssh_test04.txt', 'w') as f:
            data = 'test ssh client copy_file function\n'
            f.write(data)

        self.info("use copy_file to copy ssh_test04.txt from local machine to remote one")
        self.SSH_CLIENT.file_copy("/tmp/ssh_test04.txt", "/tmp/ssh_test04.txt")

        self.info("check that file is copy in the remote machine or not")
        output, error = self.os_command('sshpass -p {} ssh {}@{} -p {} "cat /tmp/ssh_test04.txt"'
                                        .format(self.passwd, self.login, self.addr, self.port))
        self.assertEqual("test ssh client copy_file function\n", output.decode())

    def test005_file_copy_non_valid_file_local_and_valid_file_remote(self):
        """
        TC 486
        Test Case for file_copy method, non valid local file and valid remote file, should fail.

        **Test scenario**
        #. try to copy non valid local file, to remote file, should fail.
        """

        self.info("try to copy non valid local file to remote valid file")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.copy_file("/tmp/NOT_VALID", "/tmp/ssh")

    def test006_file_copy_directory_local_and_valid_file_remote(self):
        """
        TC 487
        Test Case for file_copy method for directory in local machine, should fail

        **Test scenario**
        #. create a directory in local machine.
        #. try to copy the directory to remote file it should fail.
        """

        self.info("create a directory in local machine ")
        output, error = self.os_command("mkdir /tmp/ssh_test06/")
        self.assertFalse(error)

        self.info("try to copy the directory to remote file it should fail.")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.copy_file("/tmp/ssh_test06/", "/tmp/ssh")

    def test007_file_copy_file_local_and_dir_remote(self):
        """
        TC 488
        Test Case for test copy_file method for valid local file with the same name as a destination directory.

        **Test scenario**
        #. create a directory in remote machine with name ssh_test07 in /tmp/
        #. create a file with the same name in local machine.
        #. try to use copy_file to copy this file from local machine to remote one, should fail.
        """
        self.info("create a directory in remote machine with name ssh_test07 in /tmp/")
        self.os_command('sshpass -p {} ssh {}@{} -p {} "mkdir /tmp/ssh_test07"'
                        .format(self.passwd, self.login, self.addr, self.port))

        self.info("create a file with name ssh_test_DIR in local machine")
        self.os_command("touch /tmp/ssh_test07")

        self.info("try to use copy_file to copy this file from local machine to remote one, should fail.")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.copy_file("/tmp/ssh_test07", "/tmp/")

    def test008_download_with_valid_source_valid_dest_none_ignoredir_none_ignorefiles_recursive_True(self):
        """
        TC 491
        Test Case to test download method in ssh client

        **Test scenario**
        #. create a file in a directory in remote machine, with certain file name.
        #. use download method to copy this directory in my local machine in /tmp/ssh_test/.
        #. check if files is downloaded or not.
        """

        self.info("create a file in a directory in remote machine, with certain file name.")
        self.os_command('sshpass -p {} ssh {}@{} -p {} "mkdir  /tmp/ssh_test08/"'
                        .format(self.passwd, self.login, self.addr, self.port))
        self.os_command('sshpass -p {} ssh {}@{} -p {} "touch /tmp/ssh_test08/test1 /tmp/ssh_test08/test2"'
                        .format(self.passwd, self.login, self.addr, self.port))

        self.info("use download method to copy this directory in my local machine in /tmp/ssh_test08/")
        self.SSH_CLIENT.download(source="/tmp/ssh_test08/", dest="/tmp/ssh_test08/")

        self.info("check if files is downloaded or not")
        output, error = self.os_command('ls /tmp/ssh_test08/')
        self.assertFalse(error)
        self.assertEqual("test1\ntest2\n", output.decode())

    def test009_download_with_valid_source_valid_dest_none_ignoredir_none_ignorefiles_recursive_False(self):
        """
        TC 502
        Test Case to test download method in ssh client

        **Test scenario**
        #. create a files in a directory in remote machine, with certain file name.
        #. use download method to copy this directory in my local machine in /tmp/test_ssh/.
        #. check if files is downloaded or not.
        """

        self.info("create a file in a directory in remote machine, with certain file name.")
        self.os_command('sshpass -p {} ssh {}@{} -p {} "mkdir  /tmp/ssh_test09/test1/test2 -p"'
                        .format(self.passwd, self.login, self.addr, self.port))
        self.os_command(
            'sshpass -p {} ssh {}@{} -p {} "touch /tmp/ssh_test09/test09_1 /tmp/ssh_test09/test1/test2/test3"'
            .format(self.passwd, self.login, self.addr, self.port))

        self.info("use download method to copy this directory in my local machine in /tmp/ssh_test09/")
        self.SSH_CLIENT.download(source="/tmp/ssh_test09/", dest="/tmp/ssh_test09/", recursive=False)

        self.info("check if files is downloaded or not")
        output, error = self.os_command('ls /tmp/ssh_test09/')
        self.assertFalse(error)
        self.assertEqual("test09_1\n", output.decode())

    def test010_download_with_valid_source_valid_dest_with_ignoredir_with_ignorefiles_recursive_True(self):
        """
        TC 503
        Test Case to test download method in ssh client

        **Test scenario**
        #. create a files in a directory in remote machine, with certain file name.
        #. use download method to copy this directory in my local machine in /tmp/ssh_test10/.
        #. check if files is downloaded or not.
        """

        self.info("create a file in remote directory in remote machine, with certain file name.")
        self.os_command('sshpass -p {} ssh {}@{} -p {} "mkdir  /tmp/ssh_test10/test1 /tmp/ssh_test10/test2 -p"'
                        .format(self.passwd, self.login, self.addr, self.port))
        self.os_command(
            'sshpass -p {} ssh {}@{} -p {} "touch /tmp/ssh_test10/test10_1 /tmp/ssh_test10/test10_2"'
            .format(self.passwd, self.login, self.addr, self.port)
        )

        self.info("use download method to copy this directory in my local machine in /tmp/ssh_test10/")
        self.SSH_CLIENT.download(
            source="/tmp/ssh_test10/",
            dest="/tmp/ssh_test10/",
            recursive=True,
            ignoredir=["test2"],
            ignorefiles=["test10_2"]
        )

        self.info("check if files is downloaded or not")
        output, error = self.os_command('ls /tmp/ssh_test10/')
        self.assertFalse(error)
        self.assertEqual("test1\ntest10_1\n", output.decode())

    def test011_download_with_non_valid_source_should_fail(self):
        """
        TC 503
        Test Case to test download method in ssh client

        **Test scenario**
        #. try to use download method with non valid source should fail.
        """
        self.info("try to use download method with non valid source should fail")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.download(source="non-valid", dest="/tmp")

    def test012_upload_with_valid_source_valid_dest_none_ignoredir_none_ignorefiles_recursive_True(self):
        """
        TC 491
        Test Case to test upload method in ssh client

        **Test scenario**
        #. create a file in a directory in a local machine, with certain file name.
        #. use upload method to copy this directory in my local machine in /tmp/ssh_test12/.
        #. check if files is uploaded or not.
        """

        self.info("create a file in a directory in local machine, with certain file name.")
        self.os_command("mkdir  /tmp/ssh_test12/")
        self.os_command("touch /tmp/ssh_test12/test1 /tmp/ssh_test12/test2")

        self.info("use upload method to copy this directory in my local machine in /tmp/test_ssh/")
        self.SSH_CLIENT.upload(source="/tmp/ssh_test12/", dest="/tmp/ssh_test12/")

        self.info("check if files is downloaded or not")
        output, error = self.os_command('sshpass -p {} ssh {}@{} -p {} "ls /tmp/ssh_test12/"'
                                        .format(self.passwd, self.login, self.addr, self.port))
        self.assertFalse(error)
        self.assertEqual("test1\ntest2\n", output.decode())

    def test013_upload_with_valid_source_valid_dest_none_ignoredir_none_ignorefiles_recursive_False(self):
        """
        TC 506
        Test Case to test upload method in ssh client

        **Test scenario**
        #. create a files in a directory in local machine, with certain file name.
        #. use upload method to copy this directory in my local machine in /tmp/ssh_test13/.
        #. check if files is uploaded or not.
        """

        self.info("create a file in a directory in local machine, with certain file name.")
        self.os_command("mkdir  /tmp/ssh_test13/test1/test2 -p")
        self.os_command("touch /tmp/ssh_test13/test13_1 /tmp/ssh_test13/test1/test2/test3")

        self.info("use upload method to copy this directory from my local machine in /tmp/ssh_test13/")
        self.SSH_CLIENT.upload(source="/tmp/ssh_test13/", dest="/tmp/ssh_test13/", recursive=False)

        self.info("check if files is uploaded or not")
        output, error = self.os_command('sshpass -p {} ssh {}@{} -p {} "ls /tmp/ssh_test13/"'
                                        .format(self.passwd, self.login, self.addr, self.port))
        self.assertFalse(error)
        self.assertEqual("test13_1\n", output.decode())

    def test014_upload_with_valid_source_valid_dest_with_ignoredir_with_ignorefiles_recursive_True(self):
        """
        TC 507
        Test Case to test upload method in ssh client

        **Test scenario**
        #. create a files in a directory in local machine, with certain file name.
        #. use upload method to copy this directory in from my local machine in /tmp/ssh_test14/.
        #. check if files is uploaded or not.
        """

        self.info("create a file in a directory in remote machine, with certain file name.")
        self.os_command("mkdir /tmp/ssh_test14/test1/ /tmp/ssh_test14/test2/ -p")

        self.os_command("touch /tmp/ssh_test14/test14_1 /tmp/ssh_test14/test14_2")

        self.info("use upload method to copy this directory in my local machine in /tmp/ssh_test14/")
        self.SSH_CLIENT.upload(
            source="/tmp/ssh_test14/",
            dest="/tmp/ssh_test14/",
            recursive=True,
            ignoredir=["test2"],
            ignorefiles=["test14_2"])

        self.info("check if files is uploaded or not")
        output, error = self.os_command('sshpass -p {} ssh {}@{} -p {} "ls /tmp/ssh_test14/"'
                                        .format(self.passwd, self.login, self.addr, self.port))
        self.assertFalse(error)
        self.assertIn("test1\ntest14_1", output.decode())

    def test015_upload_with_non_valid_source_should_fail(self):
        """
        TC 508
        Test Case to test upload method in ssh client

        **Test scenario**
        #. try to use upload method with non valid source should fail.
        """
        self.info("try to use upload method with non valid source should fail")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.upload(source="non-valid", dest="/tmp/")

    def test016_execute_for_valid_command_line(self):
        """
        TC 492
        Test Case to test execute command in remote machine, should pass

        **Test scenario**
        #. use execute method to execute ( ls / ) in remote machine.
        #. check the output of this command.
        """
        self.assertIn("tmp", self.SSH_CLIENT.execute(cmd="ls /", interactive=False)[1])

    @parameterized.expand([("NON_VALID",), (None,)])
    def test017_execute_for_non_valid_and_none_command_line(self, command):
        """
        TC 493, 494
        Test Case to test execute command in remote machine, should fail

        **Test scenario**
        #. use execute method to execute ( NON_VALID and None ) in remote machine, should fail.
        """
        with self.assertRaises(Exception):
            self.SSH_CLIENT.execute(cmd=command, interactive=False)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/160")
    def test018_execute_for_script(self):
        """
        TC 512
        Test case to test execute method in ssh client method should pass.

        **Test scenario**
        #. use execute method to execute multi-lines cmd with script option == True.
        #. check that the output if this command.
        """

        self.info("use execute method to execute multi-lines cmd with script option == True")
        self.assertEqual("test_execute_script\n",
                         self.SSH_CLIENT.execute(script=True, interactive=False, cmd="""
                         touch /tmp/test_execute_script
                         ls /tmp/ | grep test_execute_script
                         """)[1]
                         )

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/160")
    def test019_ssh_authorize_with_pubkeys_option_specified_and_home_dir(self):
        """
        TC 495
        Test Case to test ssh_authorize with pubkeys option specified, and home dir, should pass.

        **Test scenario**
        #. grep pubkey from my system.
        #. use ssh_authorize to copy local pubkey to remote host.
        #. check on remote host if it copied already or not.
        """
        self.info("grep pubkey from my system")
        pubkey = open("/root/.ssh/id_rsa.pub").read()

        self.info("use ssh_authorize to copy local pubkey to remote host")
        self.SSH_CLIENT.ssh_authorize(pubkeys=pubkey, interactive=False)

        self.info("check the existence of the pubkey in the remote ssh directory")
        output, error = self.os_command('sshpass -p {} ssh root@{} -p {} "cat /root/.ssh/authorized_keys"'
                                        .format(self.passwd, self.addr, self.port))
        self.assertIn(pubkey, output.decode())

    def test020_ssh_authorize_without_pubkeys_option_specified(self):
        """
        TC 496
        Test Case to test ssh_authorize without pubkeys option specified, and home dir, should fail.

        **Test scenario**
        #. use ssh_authorize without pubkeys specified, and homedir option, should fail.
        """
        self.info("use ssh_authorize without pubkeys specified, and homedir option")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.ssh_authorize(homedir="/root/.ssh/")

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/160")
    def test021_ssh_authorize_with_pubkeys_option_specified_with_non_valid_homedir(self):
        """
        TC 501
        Test case to test ssh_authorize with pubkeys option specified, and without home dir, should fail.

        **Test scenario**
        #. use ssh_authorize to copy local pubkey to remote host with pubkeys specified, and not valid homedir.
        """
        self.info("grep pubkey from my system")
        pubkey = open("/root/.ssh/id_rsa.pub").read()

        self.info("use ssh_authorize to copy local pubkey to remote host with pubkeys specified, not valid homedir")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.ssh_authorize(pubkeys=pubkey, homedir="/NOT_VALID", interactive=False)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/204")
    def test022_portforward_to_local_valid_port(self):
        """
        TC 513
        Test case to test portforward_to_local method in ssh client

        **Test scenario**
        #. install nginx in the remote machine.
        #. make sure that nginx is installed correctly and works on port 80.
        #. use portforward_to_local method to access it from my local machine to port 99999.
        #. check that nginx is working on port 99999 from my local machine.
        """
        self.assertTrue(self.check_nginx_install())

        self.info("create portforwarding_to_local using  portforward_to_local in ssh client")
        self.SSH_CLIENT.portforward_to_local(80, 99999)

        self.info("check that port forwarding is created correctly")
        output, error = self.os_command("curl localhost:99999")
        self.assertFalse(error)
        self.assertIn("Welcome to nginx!", output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/204")
    def test023_portforward_to_local_non_valid_port(self):
        """
        TC 515
        Test case to test portfarwarding to local using used port, should fail

        **Test scenario**
        #. install nginx in the remote machine.
        #. make sure that nginx is installed correctly and works on port 80.
        #. use portforward_to_local method to access it from my local machine to port 88888.
        #. check that nginx is working on port 88888 from my local machine.
        #. use portforward_to_local method again to access it from my local machine to port 88888, should fail.
        """
        self.assertTrue(self.check_nginx_install())

        self.info("create portforwarding_to_local using  portforward_to_local in ssh client")
        self.SSH_CLIENT.portforward_to_local(80, 88888)

        self.info("check that port forwarding is created correctly")
        output, error = self.os_command("curl localhost:88888")
        self.assertFalse(error)
        self.assertIn("Welcome to nginx!", output.decode())

        self.info("use portforward_to_local method again to access it from my local machine to port 88888, should fail")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.portforward_to_local(80, 88888)

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/204")
    def test024_kill_port_forwarding(self):
        """
        TC 516
        Test case to test kill_port_forwarding method in ssh client.

        **Test scenario**
        #. create a port forwarding.
        #. try to kill this port forwarding.
        #. check that I cannot access the running Nginx after killing the port forwarding.
        """
        self.assertTrue(self.check_nginx_install())

        self.info("create port forwarding from local to remote, using portforward_to_local in ssh client")
        self.SSH_CLIENT.portforward_to_local(80, 123456)

        self.info("try to create a port forwarding using portforward_kill method")
        self.assertTrue(self.SSH_CLIENT.portforward_kill(123456))

        self.info("check that I cannot access the running Nginx after killing the port forwarding.")
        output, error = self.os_command("curl localhost:123456")
        self.assertTrue(error)
        self.assertIn("Connection refused", error.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/204")
    def test025_try_killportforwarding_doesnt_exists(self):
        """
        TC 517
        Test case to test killportforwarding method in ssh client for none exists port, should fail.

        **Test scenario**
        #. try to use killportforwarding with method in ssh client for none exists port.
        """

        self.info("try to use killportforwarding with method in ssh client for none exists port")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.portforward_kill(55555)

    def test026_syncer(self):
        """
        TC 518
        Test case to test syncer method in ssh client

        **Test scenario**
        #. create a instance from syncer method.
        #. try to list ssh_clients in this method, should return our ssh_client.
        """
        self.info("create a instance from syncer method")
        syncer = self.SSH_CLIENT.syncer

        self.info("try to list ssh_clients in this method, should return our ssh_client")
        self.assertIn(self.SSH_CLIENT.name, str(syncer.sshclient_names))

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/160")
    def test027_execute_jumpscale_for_valid_jsx_command(self):
        """
        TC 519
        Test case to test execute_jumpscale method in ssh client for valid jsx command, should pass.

        **Test scenario**
        #. use execute_jumpscale command create ssh_test28 file in /tmp directory.
        #. make sure that this file is created correctly.
        """

        self.info("use execute_jumpscale command create ssh_test28 file in /tmp directory")
        self.SSH_CLIENT.execute_jumpscale("j.sal.fs.touch(\"/tmp/ssh_test28\")")

        self.info("make sure that this file is created correctly")
        output, error = self.os_command('sshpass -p {} ssh {}@{} -p {} "ls /tmp/"'
                                        .format(self.passwd, self.login, self.addr, self.port))

        self.assertIn("ssh_test28", output.decode())

    @unittest.skip("https://github.com/threefoldtech/jumpscaleX_core/issues/160")
    def test028_execute_jumpscale_for_non_valid_jsx_command(self):
        """
        TC 520
        Test case to test execute_jumpscale method in ssh client for non valid jsx command, should fail.

        **Test scenario**
        #. use execute_jumpscale to execute non valid jsx command, should fail.
        """

        self.info("use execute_jumpscale to execute non valid jsx command")
        with self.assertRaises(Exception):
            self.SSH_CLIENT.execute_jumpscale("NON_VALID", interactive=False)
