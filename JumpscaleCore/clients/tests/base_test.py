import logging
import unittest
from subprocess import Popen, PIPE
from Jumpscale import j


class BaseTest(unittest.TestCase):
    @staticmethod
    def info(message):
        logging.basicConfig(format="%(message)s", level=logging.INFO)
        logging.info(message)

    @staticmethod
    def os_command(command):
        process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        output, error = process.communicate()
        return output, error

    @staticmethod
    def rand_num(start=100, stop=1000):
        return j.data.idgenerator.generateRandomInt(start, stop)

    @staticmethod
    def rand_string():
        return j.data.idgenerator.generateXCharID(10)
