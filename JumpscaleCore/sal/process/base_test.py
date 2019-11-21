from unittest import TestCase
from uuid import uuid4
from loguru import logger
import subprocess


class BaseTest(TestCase):
    LOGGER = logger
    LOGGER.add("SAL_PROCESS_{time}.log")

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @staticmethod
    def rand_string(size=10):
        return str(uuid4())[:size]

    @staticmethod
    def info(message):
        BaseTest.LOGGER.info(message)

    @staticmethod
    def os_command(command):
        BaseTest.info("Execute : {} ".format(command))
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()
        return output, error
