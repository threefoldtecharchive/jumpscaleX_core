import servers
import unittest
import subprocess
from loguru import logger


class BaseTest(unittest.TestCase):
    LOGGER = logger
    LOGGER.add("server_{time}.log")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.servers = servers.servers.copy()

    def info(self, message):
        BaseTest.LOGGER.info(message)

    def os_command(self, command):
        self.info("Execute : {} ".format(command))
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()
        return output, error
