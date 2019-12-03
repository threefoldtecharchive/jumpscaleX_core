import os
import uuid, random
from .base_test import BaseTest
from unittest import skip
import requests


class TestInstallationInDocker(BaseTest):
    def setUp(self):
        print("\t")
        self.CONTAINER_NAME = str(uuid.uuid4()).replace("-", "")[:10]
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

    def test09_verify_reinstall_r_option(self):
        """

        **Verify that container-install -r  works successfully **
        """
        self.install_jsx_container()
        self.info("Remove one of default installed packages using jumpscale  in existing jumpscale container")
        command = "pip3 uninstall prompt-toolkit -y"
        self.docker_command(command)

        self.info("Add data in bcdb by get new client.")
        client_name = str(uuid.uuid4()).replace("-", "")[:10]
        command = "source /sandbox/env.sh && kosmos 'j.clients.zos.get({})'".format(client_name)
        output, error = self.docker_command(command)

        self.info("Run container-install -r ")
        command = "/tmp/jsx container-install -s -n {} -r ".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)
        self.assertIn("installed successfully", output.decode())

        self.info("Check that same container exist with bcdb data and removed pacakage exist.")
        command = "source /sandbox/env.sh && kosmos 'j.data.bcdb.system.get_all()'"
        output, error = self.docker_command(command)
        self.assertTrue(data for data in output.decode() if data.name == client_name)

        command = "pip3 list | grep -F prompt-toolkit"
        output, error = self.os_command(command)
        self.assertIn("prompt-toolkit", output.decode())

    def test10_verify_scratch_option(self):
        """

        **Verify that container-install --scratch  works successfully **
        """
        self.install_jsx_container()

        self.info("Add data in bcdb by get new client.")
        client_name = str(uuid.uuid4()).replace("-", "")[:10]
        command = "source /sandbox/env.sh && kosmos 'j.clients.zos.get({})'".format(client_name)
        output, error = self.docker_command(command)

        self.info("Use container-install --scratch with same conatiner name. ")
        command = "/tmp/jsx container-install -s -n {} --scratch ".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)
        self.assertIn("installed successfully", output.decode())

        self.info("Check that new contianer installed without new data .")
        command = "source /sandbox/env.sh && kosmos 'j.data.bcdb.system.get_all()'"
        output, error = self.docker_command(command)
        self.assertFalse(data for data in output.decode() if data.name == client_name)

    def test11_verify_threebot(self):
        """

        **Verify that container-install --threebot  works successfully **
        """
        self.info("Use container-install --threebot.")
        output, error = self.jumpscale_installation(
            "container-install", "-n {} --threebot ".format(self.CONTAINER_NAME)
        )
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Check that container installed sucessfully with threboot.")
        command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % self.CONTAINER_NAME
        output, error = self.os_command(command)
        container_image = output.decode()
        self.assertIn("threefoldtech/3bot", container_image.strip("\n"))

        command = "ls /sandbox/bin"
        files_list, error = self.docker_command(command)
        threebot_builders = [{"sonic": "apps"}, {"zdb": "db"}, {"openresty": "web"}]
        for builder in threebot_builders:
            self.assertIn(list(builder.keys())[0], files_list.decode())
            command = 'source /sandbox/env.sh && kosmos -p "getattr(getattr(j.builders,\\"{}\\"),\\"{}\\").install()"'.format(
                list(builder.values())[0], list(builder.keys())[0]
            )
            output, error = self.docker_command(command)
            self.assertIn("already done", output.decode())

    def test12_verify_images(self):
        """

        **Verify that container-install --image  works successfully **
        """
        self.info("Use container-install --threebot.")
        image = "threefoldtech/3bot"
        output, error = self.jumpscale_installation(
            "container-install", "-n {} --image {} ".format(self.CONTAINER_NAME, image)
        )
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Check that container installed sucessfully with right image.")
        command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % self.CONTAINER_NAME
        output, error = self.os_command(command)
        container_image = output.decode()
        self.assertEqual(image, container_image.strip("\n"))

    def test13_verify_ports(self):
        """

        **Verify that container-install --ports  works successfully **
        """
        self.info("Use container-install --ports.")
        source_port_1 = random.randint(20, 500)
        destination_port_1 = random.randint(500, 1000)

        source_port_2 = random.randint(20, 500)
        destination_port_2 = random.randint(500, 1000)
        output, error = self.jumpscale_installation(
            "container-install",
            "-n {} --ports {}:{} {}:{} ".format(
                self.CONTAINER_NAME, source_port_1, destination_port_1, source_port_2, destination_port_2
            ),
        )
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Check that container installed sucessfully with right ports.")
        command = "docker port {}".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)
        exported_port_1 = "{}/tcp -> 0.0.0.0:{}".format(destination_port_1, source_port_1)
        exported_port_2 = "{}/tcp -> 0.0.0.0:{}".format(destination_port_2, source_port_2)
        self.assertIn(exported_port_1, output.decode())
        self.assertIn(exported_port_2, output.decode())

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/182")
    def test14_verify_branch(self):
        """

        **Verify that container-install --branch  works successfully **
        """
        self.info("Use container-install --branch.")
        branch = "master"
        output, error = self.jumpscale_installation(
            "container-install", "-n {} --branch {}".format(self.CONTAINER_NAME, branch)
        )
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Check that container installed sucessfully with right branch.")
        command = "cat /sandbox/code/github/threefoldtech/jumpscaleX_core/.git/HEAD"
        output, _ = self.docker_command(command)
        code_branch = output.decode().replace("\n", "").split("/")[-1]
        self.assertEqual(branch, code_branch)

    def test15_verify_containers(self):
        """

        **Verify that /tmp/jsx containers  works successfully **
        """
        self.install_jsx_container()

        self.info("Use /tmp/jsx containers option ")
        command = "/tmp/jsx containers"
        output, error = self.os_command(command)

        self.info("Check that container exist in containers list . ")
        self.assertIn(self.CONTAINER_NAME, output.decode())

    def test16_verify_develop(self):
        """

        **Verify that container-install --develop  works successfully **
        """
        self.info("Use container-install --develop.")
        output, error = self.jumpscale_installation("container-install", "-n {} --develop".format(self.CONTAINER_NAME))
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Check that container installed sucessfully with right development image.")
        command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % self.CONTAINER_NAME
        output, error = self.os_command(command)
        container_image = output.decode()
        self.assertIn("threefoldtech/3botdev", container_image.strip("\n"))

    def test17_verify_container_save(self):
        """

        **Verify that container-save  works successfully **
        """
        self.info("Install js container.")
        self.install_jsx_container()

        self.info(" Run container-save.")
        committed_image_name = self.rand_str()
        command = "/tmp/jsx container-save  -n {} --dest {}".format(self.CONTAINER_NAME, committed_image_name)
        output, error = self.os_command(command)

        self.info("Check that image committed successfully.")
        command = "docker images | grep %s " % committed_image_name
        output, error = self.os_command(command)
        self.assertTrue(output)

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/180")
    def test18_verify_threebot(self):
        """

        **Verify that threebot-test option  works successfully **
        """
        self.info(" Run threebot option .")
        command = "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/development/install/jsx.py?$RANDOM > /tmp/jsx"
        self.os_command(command)

        self.info("Change installer script [/tmp/jsx] to be executed ")
        command = "chmod +x /tmp/jsx"
        self.os_command(command)
        self.info("Configure the no-interactive option")
        command = "/tmp/jsx configure -s --secret mysecret"
        self.os_command(command)

        command = "/tmp/jsx threebot-test"
        output, error = self.os_command(command)

        self.info("Check that container installed sucessfully with right development image.")
        self.CONTAINER_NAME = "3bot"
        command = "docker ps -a -f status=running  | grep {}".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)
        self.assertTrue(output.decode())

        command = "ps -aux | grep startupcmd_zdb"
        output, error = self.docker_command(command)
        self.assertTrue(output)

        command = "ps -aux | grep startupcmd_sonic"
        output, error = self.docker_command(command)
        self.assertTrue(output)

    def test19_verify_basebuilder(self):
        """

        **Verify that basebuilder option  works successfully **
        """
        command = "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/development/install/jsx.py?$RANDOM > /tmp/jsx"
        self.os_command(command)

        self.info("Change installer script [/tmp/jsx] to be executed ")
        command = "chmod +x /tmp/jsx"
        self.os_command(command)

        self.info("Add sshkey ")
        self.os_command('ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa')
        self.os_command("eval `ssh-agent -s`  &&  ssh-add")

        self.info("Configure the no-interactive option")
        command = "/tmp/jsx configure -s --secret mysecret"
        self.os_command(command)

        self.info(" Run basebuilder option .")
        command = "/tmp/jsx  basebuilder "
        output, error = self.os_command(command)

        self.info("Check that base container installed sucessfully with right base image.")
        self.CONTAINER_NAME = "base"
        command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % self.CONTAINER_NAME
        output, error = self.os_command(command)
        self.assertTrue(output.decode())
        self.assertIn("threefoldtech/base", output.decode())

        self.info("install jumpscale inside the base docker, should succeed  ")
        command = "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/development/install/jsx.py?$RANDOM > /tmp/jsx"
        self.docker_command(command)
        command = "chmod +x /tmp/jsx"
        self.docker_command(command)

        self.info("Add key on base cnstainer .")
        self.docker_command('ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa')
        self.docker_command("eval `ssh-agent -s` && ssh-add")

        self.info("Configure the no-interactive option in base container .")
        command = "/tmp/jsx configure -s --secret mysecret"
        self.docker_command(command)

        command = "/tmp/jsx install -s"
        output, error = self.docker_command(command)
        self.assertIn("installed successfully", output.decode())

    def test20_verify_pull(self):
        """

        **Verify that --pull option  works successfully **
        """
        self.install_jsx_container()
        self.info("Remove created container. ")
        command = "docker rm -f {}".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)

        self.info("Checkout jumpscalex_core repo to old commit")
        command = "cd /sandbox/code/github/threefoldtech/jumpscaleX_core && git log -2"
        output, error = self.os_command(command)
        commits = output.decode().splitlines()
        latest_commit = commits[0][commits[0].find("commit") + 7 :]
        old_commit = commits[1][commits[1].find("commit") + 7 :]
        command = "cd /sandbox/code/github/threefoldtech/jumpscaleX_core && git checkout {}".format(old_commit)
        output, error = self.os_command(command)

        self.info("install jumpscale with container-install --pull ")
        output, error = self.jumpscale_installation("container-install", "-n {} --pull".format(self.CONTAINER_NAME))
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Check that jumpscalex_core repo updated.")
        command = "cd /sandbox/code/github/threefoldtech/jumpscaleX_core && git log -1"
        output, error = self.os_command(command)
        self.assertIn(latest_commit, output.decode())
        output, error = self.docker_command(command)
        self.assertIn(latest_commit, output.decode())

    def test21_verify_configure(self):
        """

        **Verify that configure options  works successfully **
        """
        self.install_jsx_container()
        self.info("Remove created container. ")
        command = "docker rm -f {}".format(self.CONTAINER_NAME)
        output, error = self.os_command(command)

        self.info("Use configure to update code directory. ")
        dire_name = "/root/test"
        command = "/tmp/jsx configure --codedir {}".format(dire_name)
        self.os_command(command)
        self.install_jsx_container()

        self.info("Check that the directory has the code now.")
        command = "ls {}/github/threefoldtech".format(dire_name)
        output, error = self.os_command(command)
        self.assertIn("jumpscaleX_core", output.decode())


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
        #. Run kosmos ,should succeedthreebotbuilder
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

    def Test02_verify_generate(self):
        """
        test TC59
        **  test jumpscale inssystem on mac or linux depending on os_type. **
        #. Run jsx generate command, should run successfully, and generate.
        """
        self.info("Install jumpscale on {}".format(self.os_type))
        output, error = self.jumpscale_installation("install")
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Check generate option, using jsx generate cmd")

        self.info("remove jumpscale_generated file")
        os.remove("rm /sandbox/lib/jumpscale/jumpscale_generated.py")

        self.info("Check generate option")
        command = ". /sandbox/env.sh && /tmp/jsx generate"
        output, error = self.os_command(command)
        self.assertIn("process", output.decode())

        self.info("make sure that jumpscale_generated file is generated again")
        self.assertTrue(os.path.exists(j.core.tools.text_replace("{DIR_BASE}/lib/jumpscale/jumpscale_generated.py")))

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

    def Test07_package_new(self):
        """
        ** test package-new  option **
        #. test that package-new option is working correctly.
        """

        self.info("Install jumpscale on {}".format(self.os_type))
        output, error = self.jumpscale_installation("install")
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("Use package-new option ")
        package_name = self.rand_str()
        destionation = "/tmp/"
        command = "/tmp/jsx  package-new --name {} --dest {}".format(package_name, destionation)
        output, error = self.os_command(command)

        self.info("chick that package added successfully.")
        command = "ls {}/{}".format(destionation, package_name)
        output, error = self.os_command(command)
        self.assertIn("actors", output.decode())
        self.assertIn("chatflows", output.decode())
        self.assertIn("models", output.decode())
        self.assertIn("wiki", output.decode())

        command = "ls {}/{}/actors".format(destionation, package_name)
        output, error = self.os_command(command)
        self.assertIn("{}.py", output.decode())

    def Test08_wiki_load(self):
        """
        ** test wikis-load  option **
        #. test that wikis-load option is working correctly.
        """

        self.info("Install jumpscale on {}".format(self.os_type))
        output, error = self.jumpscale_installation("install")
        self.assertFalse(error)
        self.assertIn("installed successfully", output.decode())

        self.info("start a threebot server. ")
        command = ". /sandbox/env.sh && kosmos -p 'j.servers.threebot.local_start_default()'"
        output, error = self.os_command(command)

        self.info("Use load-wikis option.")
        wikis_name = self.rand_str()
        wikis_url = "https://github.com/threefoldtech/jumpscaleX_threebot/tree/development/docs/wikis/examples/docs"
        command = "/tmp/jsx  wiki-load -n {} -u {}".format(wikis_name, wikis_url)
        output, error = self.os_command(command)
        self.assertFalse(error)

        self.info("Check the wikis is loaded, should be found.")
        r = requests.get("https://127.0.0.1/wiki/test_presentaion.md", verify=False)
        self.assertEqual(r.status_code, 200)
        self.assertIn("includes 1", r.content.decode())
