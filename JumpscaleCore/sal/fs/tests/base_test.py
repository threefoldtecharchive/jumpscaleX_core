from unittest import TestCase
from uuid import uuid4

from loguru import logger


class BaseTest(TestCase):
    LOGGER = logger
    LOGGER.add("SAL_FS_{time}.log")

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @staticmethod
    def random_string():
        return str(uuid4())[:10]

    @staticmethod
    def info(message):
        BaseTest.LOGGER.info(message)
