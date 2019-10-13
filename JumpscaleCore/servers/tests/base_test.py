import unittest
import subprocess, uuid
from loguru import logger


class BaseTest(unittest.TestCase):
    LOGGER = logger
    LOGGER.add("server_{time}.log")
    SERVERS = ["corex", "etcd", "zdb", "odoo", "sonic", "sanic", "capacity", "flask", "gedis_websocket", "sockexec"]
    INSTALLED_SERVER = ["gedis", "gedis_websocket"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def info(message):
        BaseTest.LOGGER.info(message)

    @staticmethod
    def os_command(command):
        BaseTest.info("Execute : {} ".format(command))
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()
        return output, error

    def set_database_data(self, database):
        database.name = str(uuid.uuid4()).replace("-", "")[1:10]
        database.admin_email = "{}@example.com".format(database.name)
        database.admin_passwd_ = self.rand_string()

    def rand_string(self, size=10):
        return str(uuid.uuid4()).replace("-", "")[1:10]
