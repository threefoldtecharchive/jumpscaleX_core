import unittest
from uuid import uuid4

from Jumpscale import j

class BaseTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def info(message):
        j.core.tools.log(msg=message, level=20)

    @staticmethod
    def generate_random_str():
        return str(uuid4()).replace("-", "")[:10]
