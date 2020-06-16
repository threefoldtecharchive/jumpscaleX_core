import os.path
from unittest import skip
from testconfig import config
from base_test import BaseTest


class InstallationTesting(BaseTest):
    BRANCH = config["installation"]["branch"]
    EMAIL = config["installation"]["email"]
    IDENTITY = config["installation"]["identity"]
    WORDS = config["installation"]["words"]

    @classmethod
    def setUpClass(cls):
        self = cls()
        cls.info("docker Install")
        self.docker_install()

        cls.info("Check that docker is installed correctly")
        output, error = cls.os_command("docker --version")
        assert "Docker version" in output.decode(), "Command 'docker' not found"

        cls.info("Install 3sdk")
        self.install_3sdk()

        cls.info("Check that 3sdk is installed correctly")
        output, error = cls.os_command("/root/.local/bin/3sdk --help")
        assert "usage: 3sdk" in output.decode(), "3sdk doesn't installed yet"

    def setUp(self):
        print("\t")
        self.info("Test case : {}".format(self._testMethodName))

    def tearDown(self):
        self.info("Remove all dockers which have been created with image")
        command = "docker rm -f $(docker ps -a | grep \"threefoldtech/3bot2\" | cut -d " " -f 1)"
        self.os_command(command)

    @classmethod
    def tearDownClass(cls):
        cls.info("Clean the installation")
        command = "rm -rf /sandbox/"
        cls.os_command(command)

    def docker_install(self):

        self.info("Docker install in ubuntu 18.04+")
        self.info("Update the apt package index and install packages to allow apt to use a repository over HTTPS")
        self.os_command("sudo apt-get update && \
        sudo apt-get install  -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common")

        self.info("Add Docker’s official GPG key")
        self.os_command("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -")

        self.info("Set up the stable repository")
        self.os_command("sudo add-apt-repository \
        \"deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\"")

        self.info("Update the apt package index, and install the latest version of Docker Engine and containerd")
        self.os_command("sudo apt-get update && sudo apt-get -y install docker-ce docker-ce-cli containerd.io")

    def create_container(self, container_name, secret):
        self.info("Create a container")
        command = "/root/.local/bin/3sdk container install name={} explorer=none secret={}" \
            .format(container_name, secret)
        output, error = self.os_command(command)

        self.info("Check that the JSX has been installed correctly")
        self.assertIn("Jumpscale X installed successfully", output.decode())

        self.info("Check that container has been created correctly")
        command = "docker ps -a -f status=running  | grep {}".format(container_name)
        output, error = self.os_command(command)
        if container_name in output.decode():
            return True
        else:
            return False

    def install_3sdk(self):
        self.info("Install pip3")
        self.os_command("sudo apt install  -y python3-pip")

        self.info("Clone jumpscale_core repo")
        CLONE_DIR = "/sandbox/code/github/threefoldtech/jumpscaleX_core"
        self.os_command("git clone -b {} https://github.com/threefoldtech/jumpscaleX_core/ {}"
                        .format(self.BRANCH, CLONE_DIR))

        self.info("Install 3sdk")
        self.os_command("cd {}/install && pip3 install --user -e .".format(CLONE_DIR))

    def test01_container_delete(self):
        """
        Test container delete.

        #. Create a container.
        #. Check that the container has been created correctly.
        #. Use delete argument with name option to delete the created container.
        #. Check that the container is has been deleted.
        #. Create two containers.
        #. Use delete argument without name option to delete the last two containers.
        #. Check that the two containers has been delete

        """
        self.info("Create three containers")
        self.info("Check that container has been created correctly")

        container_1 = self.rand_string()
        self.assertTrue(self.create_container(container_1, container_1),
                        "{} doesn't created correctly".format(container_1))
        self.info("Use delete argument with name option to delete the created container")
        command = "/root/.local/bin/3sdk container delete name={}".format(container_1)
        self.os_command(command)

        self.info("Check that container has been deleted correctly")
        command = "docker ps -a | grep {}".format(container_1)
        output, error = self.os_command(command)
        self.assertNotIn(container_1, output.decode())

        self.info("Create another container")
        container_2 = self.rand_string()
        self.assertTrue(self.create_container(container_2, container_2),
                        "{} doesn't created correctly".format(container_2))

        self.info("Use delete argument without name option to delete the container")
        command = "/root/.local/bin/3sdk container delete".format(container_2)
        self.os_command(command)

        self.info("Check that the container has been deleted correctly")
        command = "docker ps -a | grep {}".format(container_2)
        output, error = self.os_command(command)
        self.assertNotIn(container_2, output.decode())

    def test02_container_stop(self):
        """
        Test stop container.

        #. Create three containers.
        #. Check that created containers are up and running.
        #. Use stop option with name argument to stop one of them.
        #. Check that container has been stopped correctly.
        #. Use stop without name argument and make sure that the other two containers have been stopped correctly.
        """

        self.info("Create three containers")
        self.info("Check that created containers are up and running")

        container_name = self.rand_string()
        for i in range(3):
            container = "{}_{}".format(container_name, i)
            self.assertTrue(self.create_container(container, container),
                            "{} doesn't created correctly".format(container))

        self.info("Use stop option with name argument to stop one of them")
        container_1 = "{}_0".format(container_name)
        command = "/root/.local/bin/3sdk container stop name={}".format(container_1)
        self.os_command(command)
        self.info("Check that container has been stopped correctly")
        command = "docker ps | grep {}".format(container_1)
        output, error = self.os_command(command)
        self.assertNotIn(container_1, output.decode())

        self.info("Use stop without name argument")
        self.info("make sure that the other two containers have been stopped correctly")
        for i in range(1, 3):
            container = "{}_{}".format(container_name, i)
            self.assertTrue(self.create_container(container, container),
                            "{} doesn't created correctly".format(container))

        command = "/root/.local/bin/3sdk container stop"
        self.os_command(command)

        for i in range(1, 3):
            command = "docker ps | grep {}_{}".format(container_name, i)
            output, error = self.os_command(command)
            self.assertNotIn("{}_{}".format(container_name, i), output.decode())

    def test03_container_start(self):
        """
        Test start container

        #. Create Two containers, one with 3bot name and the other with another name.
        #. Use stop argument to stop both container.
        #. Use start without -name to start the 3bot container.
        #. Use start with -name to start the other container.
        #. Check that both containers have been started correctly.

        """
        self.info("Create Two containers, one with 3bot name and the other with another name")
        container_name = self.rand_string()
        self.assertTrue(self.create_container(container_name, container_name),
                        "{} doesn't created correctly".format(container_name))
        self.assertTrue(self.create_container("3bot", "123"), "3bot container doesn't created correctly")

        self.info("Use stop argument to stop both container")
        command = "/root/.local/bin/3sdk container stop"
        self.os_command(command)

        self.info("Use start without -name to start the 3bot container")
        command = "/root/.local/bin/3sdk container start"
        self.os_command(command)
        self.info("Use start with -name to start the 3bot container")
        command = "/root/.local/bin/3sdk container start name={}".format(container_name)
        self.os_command(command)

        self.info("Check that both containers have been started correctly")
        for container in (container_name, "3bot"):
            command = "docker ps | grep {}".format(container)
            output, error = self.os_command(command)
            self.assertIn(container, output.decode())

    def test04_container_list(self):
        """
        Test list containers

        #. Create a container using 3sdk.
        #. Create another container using normal docker command.
        #. Use list command to list the container.
        #. Check that list command lists only the container which created by threefoldtech/3bot2.
        """

        self.info("Create a container using 3sdk")
        container_name = self.rand_string()
        self.assertTrue(self.create_container(container_name, container_name),
                        "{} doesn't created correctly".format(container_name))

        self.info("Create another container using normal docker command")
        container_name_2 = self.rand_string()
        command = "docker container create --name \"{}\" ubuntu:latest".format(container_name_2)
        output, error = self.os_command(command)
        self.assertFalse(error)

        self.info("Use list command to list the container")
        self.info("Check that list command lists only the container which created by threefoldtech/3bot2")
        command = "/root/.local/bin/3sdk container list"
        output, error = self.os_command(command)
        self.assertIn(container_name, output.decode())
        self.assertNotIn(container_name_2, output.decode())

    @skip("https://github.com/threefoldtech/jumpscaleX_core/issues/895")
    def test05_container_install(self):
        """
        Test container install

        #. Create a container using 3sdk.
        #. Check that the JSX has been installed correctly.
        #. Check that container is created correctly.

        """

        self.info("Create a container using 3sdk")
        container_name = self.rand_string()
        container_secret = self.rand_string()
        command = '/root/.local/bin/3sdk container install email="{}" identity="{}" words="{}" name="{}" ' \
                  'explorer=explorer.testnet.grid.tf secret="{}"' \
            .format(self.EMAIL, self.IDENTITY, self.WORDS, container_name, container_secret)
        output, error = self.os_command(command)

        self.info("Check that the JSX has been installed correctly")
        self.assertIn("Jumpscale X installed successfully", output.decode())

        self.info("Check that container has been created correctly")
        command = "docker ps | grep {}".format(container_name)
        output, error = self.os_command(command)
        self.assertIn(container_name, output.decode())

    def test06_builder_container_export(self):
        """
        Test export the 3bot to image file.

        #. Export image to certain path.
        #. Check that image has been exported correctly.

        """

        self.info("Export image to certain path")
        version_number = self.rand_string()
        command = "/root/.local/bin/3sdk builder container_export version=\"{}\"".format(version_number)
        output, error = self.os_command(command)

        self.assertFalse(error)
        self.assertIn("export docker:3bot to /sandbox/var/containers/3bot/exports/{}.tar".format(version_number),
                      output.decode())

        self.info("Check that image has been exported correctly")
        self.assertTrue(os.path.isfile("/sandbox/var/containers/3bot/exports/{}.tar".format(version_number)))

    def test07_builder_container_import(self):
        """
        Test import container from image file.

        #. Export image to certain path.
        #. Import image from the path.
        #. Check the image is imported correctly.
        """
        version_number = self.rand_string()
        command = "/root/.local/bin/3sdk builder container_export version={}".format(version_number)
        output, error = self.os_command(command)
        self.assertFalse(error)

        self.info("Import image from the path")
        command = "/root/.local/bin/3sdk builder container_import path=\"/sandbox/var/containers/3bot/exports/{}.tar\""\
            .format(version_number)
        output, error = self.os_command(command)

        self.info("Check the image is imported correctly")
        lines = output.decode().splitlines()
        for line in lines:
            if line.startswith('sha256'):
                docker_image = line

        output, error = self.os_command("docker images --no-trunc | grep {}".format(docker_image))
        self.assertIn(docker_image, output.decode())
