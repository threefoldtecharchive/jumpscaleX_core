import os
import uuid
from .base_test import BaseTest
from unittest import skip


class TestInstallationInDocker(BaseTest):
    def setUp(self):
        print("\t")
        self.info("Test case : {}".format(self._testMethodName))

    def tearDown(self):
        self.info("Clean the installation")
        command = "rm -rf /sandbox/ ~/sandbox/ /tmp/jsx /tmp/jumpscale/ /tmp/InstallTools.py"
        self.os_command(command)
        self.info("Delete jumpscale created container.")
        command = "docker rm -f {}".format(self.CONTAINER_NAME)
        self.os_command(command)

        command = "rm -rf /sandbox; rm -rf ~/sandbox"
        self.os_command(command)

    def install_jsx_container(self):
        self.CONTAINER_NAME = str(uuid.uuid4()).replace("-", "")[:10]
        self.info("Install container jumpscale in {} os type".format(self.get_os_type()))
        output, error = self.jumpscale_installation("container-install", "-n {}".format(self.CONTAINER_NAME))
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

    def Test01_verify_container_kosmos_option(self):
        """
        TC54

        ** Test installation of container jumpscale on linux or mac depending on os_type **

        *Test libs builers sandbox*
        #. Install jumpscale from specific branch
        #. Run container-kosmos ,should succeed
        """
        self.install_jsx_container()
        self.info("Run container_kosmos ,should succeed")
        command = " echo 'from Jumpscale import j' | /tmp/jsx container-kosmos -n {}".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)
        self.assertFalse(error)
        self.assertIn("BCDB INIT DONE", output.decode())

    def Test02_verify_container_stop_start_options(self):
        """
        TC48,TC55
        ** test  container-stop and container-start options on mac or linux depending on os_type **

        #. Check that js container exist ,should succeed.
        #. Run container stop.
        #. Check that container stopped successfully.
        #. Run container started.
        #. Check that container started successfully

        """
        self.install_jsx_container()
        self.info(" Running on {} os type".format(self.os_type))

        self.info("Run container stop ")
        command = "/tmp/jsx container-stop -n {}".format(self.CONTAINER_NAME)
        self.os_command(command)

        self.info("Check that container stopped successfully")
        command = "docker ps -a -f status=running  | grep {}".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)
        self.assertFalse(output)

        self.info("Run container started ")
        command = "/tmp/jsx container-start -n {}".format(self.CONTAINER_NAME)
        self.os_command(command)

        self.info("Check that container started successfully")
        command = "docker ps -a -f status=running  | grep {}".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)
        self.assertIn(self.CONTAINER_NAME, output.decode())

    def Test03_verify_jsx_working_inside_docker(self):
        """
        TC51,TC56
        ** test jumpscale inside docker on mac or linux depending on os_type. **

        #. Run kosmos command inside docker, should start kosmos shell .
        #. Run js_init generate command inside docker, sshould run successfully.
        #. Check the branch of jumpscale code, should be same as installation branch.
        """
        self.install_jsx_container()
        self.info("Run kosmos command inside docker,should start kosmos shell")
        command = """source /sandbox/env.sh && kosmos "from Jumpscale import j;print(j)" """
        output, error = self.docker_command(command)
        self.assertIn("Jumpscale.Jumpscale object", output.decode())

        self.info("Run js_init generate ")
        command = "source /sandbox/env.sh && js_init generate"
        output, error = self.docker_command(command)
        self.assertFalse(error)
        self.assertIn("process", output.decode())

        self.info(" Check the branch of jumpscale code, should be same as installation branch.")
        command = "cat /sandbox/code/github/threefoldtech/jumpscaleX_core/.git/HEAD"
        output, _ = self.docker_command(command)
        branch = output.decode().replace("\n", "").split("/")[-1]
        self.assertEqual(branch, "development")

        self.info("check  that ssh-key loaded in docker successfully")
        command = "cat /root/.ssh/authorized_keys"
        output, error = self.docker_command(command)
        for key in self.get_loaded_key().split("\n"):
            self.assertIn(key, output.decode().strip("\n"))

    def test04_verify_container_delete_option(self):
        """

        **Verify that container-delete option will delete the running container**
        """
        self.install_jsx_container()
        self.info("Delete the running jsx container using container-delete")
        command = "/tmp/jsx container-delete -n {}".format(self.CONTAINER_NAME)
        self.os_command(command)

        command = "docker ps -a | grep {}".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)
        self.assertFalse(output)

    def test05_verify_containers_reset_option(self):
        """

        **Verify that containers-reset option will delete running containers and image**
        """
        self.install_jsx_container()
        self.info("Reset the running container and image using container-reset")
        command = "/tmp/jsx containers-reset".format(self.CONTAINER_NAME)
        self.os_command(command)

        self.info("Check that running containers have been deleted")
        command = "docker ps -aq "
        output, error = self.os_command(command)
        self.assertFalse(output)

        self.info("Check that containers image have been deleted")
        command = "docker images -aq "
        output, error = self.os_command(command)
        self.assertFalse(output)

    def test06_verify_containers_import_export_options(self):
        """

        **Verify that container-import and container-export works successfully **
        """
        self.install_jsx_container()
        self.info("Use container-export ,should export the running container.")
        command = "/tmp/jsx container-export -n {}".format(self.CONTAINER_NAME)
        self.os_command(command)

        self.info("Create file in existing jumpscale container")
        file_name = str(uuid.uuid4()).replace("-", "")[:10]
        command = "cd / && touch {}".format(file_name)
        self.docker_command(command)

        self.info("Use container-import, should restore the container")
        command = "/tmp/jsx container-import -n {}".format(self.CONTAINER_NAME)
        self.os_command(command)

        self.info("Check that container does not have the file ")
        command = "ls / "
        output, error = self.docker_command(command)
        self.assertNotIn(file_name, output.decode())

    # @skip("To re-do")
    # def test07_verify_container_clean_options(self):
    #     """

    #     **Verify that container-clean works successfully **
    #     """
    #     self.install_jsx_container()
    #     command = 'docker ps -a | grep %s | awk "{print \$2}"' % self.CONTAINER_NAME
    #     output, error = self.os_command(command)
    #     container_image = output.decode()

    #     self.info("Run container stop ")
    #     command = "/tmp/jsx container-stop -n {}".format(self.CONTAINER_NAME)
    #     self.os_command(command)

    #     self.info("Run container-clean with new name")
    #     new_container = str(uuid.uuid4()).replace("-", "")[:10]
    #     command = "/tmp/jsx container-clean -n {}".format(new_container)
    #     output, error = self.os_command(command)
    #     self.assertIn("import docker", output.decode())

    #     self.info("Check that new container created with same image")
    #     command = "ls /sandbox/var/containers/{}/exports/".format(new_container)
    #     output, error = self.os_command(command)
    #     self.assertFalse(error)
    #     self.assertIn("tar", output.decode())

    #     command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % self.CONTAINER_NAME
    #     output, error = self.os_command(command)
    #     new_container_image = output.decode()
    #     self.assertEqual(container_image, new_container_image)

    def test08_verify_reinstall_d_option(self):
        """

        **Verify that container-install -d  works successfully **
        """
        self.install_jsx_container()
        self.info("Create file in existing jumpscale container")
        file_name = str(uuid.uuid4()).replace("-", "")[:10]
        command = "cd / && touch {}".format(file_name)
        self.docker_command(command)

        self.info("Run container-install -d ")
        command = "/tmp/jsx container-install -s -n {} -d  ".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)
        self.assertIn("installed successfully", output.decode())

        self.info("Check that new container created with same name and created file doesn't exist")
        command = "ls / "
        output, error = self.docker_command(command)
        self.assertNotIn(file_name, output.decode())


class TestInstallationInSystem(BaseTest):
    def setUp(self):
        print("\t")
        self.info("Test case : {}".format(self._testMethodName))

    def tearDown(self):
        self.info("Clean the installation")
        command = "rm -rf /sandbox/ ~/sandbox/ /tmp/jsx /tmp/jumpscale/ /tmp/InstallTools.py"
        self.os_command(command)

    def Test01_install_jumpscale_insystem_no_interactive(self):
        """
        test TC58
        ** Test installation of Jumpscale using insystem non-interactive option on Linux or mac OS **
        #. Install jumpscale from specific branch
        #. Run kosmos ,should succeed
        """
        self.info("Install jumpscale on {}".format(self.os_type))
        output, error = self.jumpscale_installation("install")
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Run kosmos shell,should succeed")
        command = ". /sandbox/env.sh && kosmos 'from Jumpscale import j; print(j)'"
        output, error = self.os_command(command)
        self.assertFalse(error)
        self.assertIn("Jumpscale.Jumpscale object", output.decode())

    # @skip("Not exist anymore jumpscale_generated.py")
    # def Test02_verify_jsx_working_insystem(self):
    #     """
    #     test TC59
    #     **  test jumpscale inssystem on mac or linux depending on os_type. **
    #     #. Run jsx generate command, should run successfully, and generate.
    #     """
    #     self.info("Install jumpscale on {}".format(self.os_type))
    #     output, error = self.jumpscale_installation("install")
    #     self.assertFalse(error)
    #     self.assertIn("installed successfully", output.decode())

    #     self.info("Check generate option, using jsx generate cmd")

    #     self.info("remove jumpscale_generated file")
    #     os.remove("/sandbox/code/github/threefoldtech/jumpscaleX/Jumpscale/jumpscale_generated.py")

    #     self.info("Check generate option")
    #     command = ". /sandbox/env.sh && jsx generate"
    #     self.os_command(command)

    #     self.info("make sure that jumpscale_generated file is generated again")
    #     self.assertTrue(
    #         os.path.exists("/sandbox/code/github/threefoldtech/jumpscaleX/Jumpscale/jumpscale_generated.py")
    #     )

    def Test03_insystem_installation_r_option_no_jsx_before(self):
        """
        test TC73, TC85
        ** Test installation of Jumpscale using insystem non-interactive and re_install option on Linux or mac OS **
        ** with no JSX installed before **
        #. Install jumpscale from specific branch
        #. Run kosmos ,should succeed
        """

        self.info("Install jumpscale on {} using no_interactive and re-install".format(self.os_type))
        output, error = self.jumpscale_installation("install", "-r")
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info(" Run kosmos shell,should succeed")
        command = ". /sandbox/env.sh && kosmos 'from Jumpscale import j; print(j)'"
        output, error = self.os_command(command)
        self.assertFalse(error)
        self.assertIn("Jumpscale.Jumpscale object", output.decode())

    def Test04_insystem_installation_r_option_jsx_installed_before(self):
        """
        test TC74, TC86
        ** Test installation of Jumpscale using insystem non-interactive and re_install option on Linux or mac OS **
        ** with JSX installed before **
        #. Install jumpscale from specific branch
        #. Run kosmos ,should succeed
        """

        self.info("Install jumpscale on {}".format(self.os_type))
        output, error = self.jumpscale_installation("install")
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Install jumpscale on {} using no_interactive and re-install".format(self.os_type))

        output, error = self.jumpscale_installation("install", "-r")
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info(" Run kosmos shell,should succeed")
        command = ". /sandbox/env.sh && kosmos 'from Jumpscale import j; print(j)'"
        output, error = self.os_command(command)
        self.assertFalse(error)
        self.assertIn("Jumpscale.Jumpscale object", output.decode())

    # @skip("Not found anymore bcdb-system-delete")
    # def Test05_bcdb_system_delete_option(self):
    #     """
    #     test TC203, TC204
    #     ** test bcdb_system_delete option on Linux and Mac OS **
    #     #. Create an instance from github client; get it
    #     #.  destroy; make sure it doesn't exist
    #     """

    #     self.info("Install jumpscale on {}".format(self.os_type))
    #     output, error = self.jumpscale_installation("install")
    #     self.assertFalse(error)
    #     self.assertIn("installed successfully", output.decode())

    #     self.info("use kosmos to create github client, make sure that there is no error")
    #     client_name = str(uuid.uuid4()).replace("-", "")[:10]
    #     command = """. /sandbox/env.sh && kosmos 'c=j.clients.github.new("{}", token="test_bcdb_delete_option"); c.save()'""".format(
    #         client_name
    #     )
    #     output, error = self.os_command(command)
    #     self.assertFalse(error)

    #     self.info("check that the client is existing")
    #     command = """. /sandbox/env.sh && kosmos 'print(j.clients.github.get("{}").name)'""".format(
    #         client_name
    #     )
    #     output, error = self.os_command(command)
    #     self.assertFalse(error)
    #     self.assertIn(client_name, output.decode())

    #     self.info("use bcdb_system_delete option to delete database, and check if the client still exists or not")
    #     command = ". /sandbox/env.sh && /tmp/jsx bcdb-system-delete"
    #     output, error = self.os_command(command)
    #     self.assertFalse(error)

    #     self.info("check that the client is not existing")
    #     command = """. /sandbox/env.sh && kosmos 'print(j.clients.github.get("{}").name)'""".format(
    #         client_name
    #     )
    #     output, error = self.os_command(command)
    #     self.assertIn("Missing Github token or login/password", output.decode())

    def Test06_check_option(self):
        """
        test TC205, TC206
        ** test check option on Linux and Mac OS **
        #. test that check option is working correctly.  
        #. check option ,ake sure that secret, private key, bcdband kosmos are working fine.
        """

        self.info("Install jumpscale on {}".format(self.os_type))
        output, error = self.jumpscale_installation("install")
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("test jsx check option ")
        command = ". /sandbox/env.sh && jsx check"
        output, error = self.os_command(command)
        self.assertFalse(error)
