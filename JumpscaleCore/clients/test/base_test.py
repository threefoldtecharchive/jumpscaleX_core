import unittest
from loguru import logger


class BaseTest(unittest.TestCase):
    LOGGER = logger
    LOGGER.add("installtion_{time}.log")
    REPO_LOCATION = "/opt/code/github/threefoldtech/jumpscaleX_core"

    @staticmethod
    def info(message):
        BaseTest.LOGGER.info(message)

