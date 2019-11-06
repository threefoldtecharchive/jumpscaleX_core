import unittest
import subprocess
from loguru import logger
import platform


class BaseTest(unittest.TestCase):
    LOGGER = logger
    LOGGER.add("installtion_{time}.log")
    REPO_LOCATION = "/opt/code/github/threefoldtech/jumpscaleX"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.js_branch = self.get_js_branch()
        self.os_type = self.get_os_type()

    @staticmethod
    def info(message):
        BaseTest.LOGGER.info(message)

    @staticmethod
    def get_loaded_key():
        command = "ssh-add -L"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        output, error = process.communicate()
        return output.decode().strip()

    # @staticmethod
    # def get_js_branch():
    #     command = "cd {} && cat .git/HEAD".format(BaseTest.REPO_LOCATION)
    #     output, error = BaseTest.os_command(command)
    #     branch = output.decode()[output.decode().find("head") + 6 : -1]
    #     return branch

    @staticmethod
    def get_os_type():
        os = platform.system()
        if os == "Darwin":
            return "Mac"
        return os

    @staticmethod
    def os_command(command):
        BaseTest.info("Execute : {} ".format(command))
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()
        return output, error

    def docker_command(self, command):
        command = "docker exec -i {} /bin/bash -c '{}'".format(self.CONTAINER_NAME, command)
        return BaseTest.os_command(command)

    @staticmethod
    def jumpscale_installation(install_type, options=" "):
        BaseTest.info("copy installation script to /tmp")
        command = "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/development/install/jsx.py?$RANDOM > /tmp/jsx"
        BaseTest.os_command(command)

        BaseTest.info("Change installer script [/tmp/jsx] to be executed ")
        command = "chmod +x /tmp/jsx"
        BaseTest.os_command(command)
        BaseTest.info("Configure the no-interactive option")
        command = "/tmp/jsx configure -s --secret mysecret"
        BaseTest.os_command(command)

        BaseTest.info("Run script with {} with branch development".format(install_type))
        command = "/tmp/jsx {} -s {}".format(install_type, options)
        output, error = BaseTest.os_command(command)
        return output, error

    @staticmethod
    def is_js_container_installed():
        BaseTest.info(" Check that js container exist ,should succeed")
        command = "/tmp/jsx container-kosmos"
        output, error = BaseTest.os_command(command)
        if "installed successfully" in output.decode():
            return True
        else:
            return False
